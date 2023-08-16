import json
import struct
from typing import TYPE_CHECKING

import pandas as pd

import nsukit
from .base import BaseRegMw
from ..tools.logging import logging

if TYPE_CHECKING:
    from .. import NSUKit

file_context_flag = '__file__'
file_length_flag = '__filelength__'
COMMAND_LENGTH = slice(12, 16)

value_type = {
    "uint8": "B",
    "int8": "b",
    "uint16": "H",
    "int16": "h",
    "uint32": "I",
    "int32": "i",
    "float": "f",
    "double": "d"
}

value_python = {
    "uint8": int,
    "int8": int,
    "uint16": int,
    "int16": int,
    "uint32": int,
    "int32": int,
    "float": float,
    "double": float,
    "file": str,
    "file_data": str,
    "file_length": str
}

type_size = {
    "uint8": 1,
    "int8": 1,
    "uint16": 2,
    "int16": 2,
    "uint32": 4,
    "int32": 4,
    "float": 4,
    "double": 8
}

feedback_value_fmt = {
    "uint8": "%#x",
    "int8": "%d",
    "uint16": "%#x",
    "int16": "%d",
    "uint32": "%#x",
    "int32": "%d",
    "float": "%f",
    "double": "%f"
}


class ICDRegMw(BaseRegMw):
    """!
    @brief ICD控制
    @details 用于使用icd进行指令收发
    """
    fmt_mode = "="  # pack/unpack 大小端模式

    def __init__(self, kit: "NSUKit", file_name='icd.json'):
        super(ICDRegMw, self).__init__(kit)
        self._file_name = file_name
        self.icd_data = {}
        self.param = {}
        self.command = {}
        self.sequence = {}
        self.check_recv_head = False

    def config(self, *, icd_path=None, check_recv_head=False, **kwargs):
        """!
        @brief 配置icd路径
        @details 指定icd配置文件的路径，并加载icd
        @param icd_path: icd文件路径
        @param check_recv_head: 自动检查指令返回包头默认不检查
        @param kwargs: 其他参数
        @return:
        """
        if icd_path is None:
            icd_path = nsukit.__file__
            icd_path = icd_path.replace('__init__.py', 'icd.json')
        self._file_name = icd_path
        self.check_recv_head = check_recv_head
        self.load()

    def load(self):
        """!
        @brief  加载icd
        @details 根据icd文件加载参数指令等
        @return: True/False
        """
        file_path = self._file_name
        with open(file_path, 'r', encoding='utf-8') as fp:
            try:
                self.icd_data = json.load(fp)
            except json.decoder.JSONDecodeError as e:
                logging.error(msg=f'{e}, {self._file_name} unavailable')
                return False
        try:
            self.param = self.icd_data['param']
            self.command = self.icd_data['command']
            self.sequence = self.icd_data['sequence']
            logging.info(msg='ICD Parameters loaded successfully')
        except Exception as e:
            logging.error(msg=f'{e},{file_path} unavailable')
            return False
        return True

    def save(self, path=''):
        """!
        @brief 保存icd
        @details 将当前运行icd参数以另一个名称进行保存
        @param path: 文件路径
        @return: True
        """
        # todo: ICD的保存怎么在nsukit中引出
        path = path + '\\' if path else path
        with open(path + self._file_name.split('.')[0] + '_run.json', 'w', encoding='utf-8') as fp:
            # 按utf-8的格式格式化并写入文件
            json.dump(self.icd_data, fp, ensure_ascii=False, indent=4)
            logging.info(msg='参数保存成功')
        return True

    def get_param(self, param_name: str, default=0, fmt_type=int):
        """!
        @brief 获取icd参数
        @details 根据参数名称获取参数值
        @param param_name: 参数名称
        @param default: 默认值
        @param fmt_type: 参数值格式化类型
        @return: 格式化后的参数值
        """
        param = self.param.get(param_name, None)
        if param[1] == "file_data" or param[1] == "file_length":
            return param[2]
        if param is None:
            logging.warning(msg=f'未找到参数：{param_name}')
            self.param.update({param_name: [param_name, 'uint32', default]})
            return fmt_type(default)
        return fmt_type(param[2])

    def set_param(self, param_name: str, value, fmt_type=int):
        """!
        @brief 设置参数值
        @details 根据参数名称设置相应的值
        @param param_name: 参数名称
        @param value: 参数值
        @param fmt_type: 参数值格式化类型
        @return:
        """
        param = self.param.get(param_name, [param_name, 'uint32', value])
        if isinstance(value, str) and value.startswith('0x'):
            param[2] = int(value, 16)
        elif isinstance(value, str) and value.startswith('0b'):
            param[2] = int(value, 2)
        elif param[1] == "file_data" or param[1] == "file_length":
            param[2] = value
        elif isinstance(value, str) and '.' in value and param[1] != 'file':
            param[2] = float(value)
        else:
            param[2] = value_python[param[1]](value)
        self.param.update({param_name: param})

    def fmt_command(self, command_name, command_type: str = "send", file_name=None) -> bytes:
        """!
        @brief 格式化指令
        @details 根据指令名、指令类型和文件名组合成指令
        @param command_name: 指令名称
        @param command_type: 指令类型(发送接收)
        @param file_name: 文件名
        @return: 格式化好的指令
        """
        file_data = b''
        command = []
        file_length = 0
        if isinstance(file_name, str):
            file_data, file_length = self.__get_file(file_name)
        try:
            target_bytes = []
            if command_name in self.sequence:
                sequence_data: pd.DataFrame = pd.read_excel(file_name)
                sequence_cmd = self.sequence[command_name]
                for row in range(sequence_data.shape[0]):
                    for register in sequence_cmd:
                        if isinstance(register, str):
                            _reg = self.param.get(register, None)
                            assert _reg, f'未找到参数{register}'
                            if register in sequence_data:
                                value = sequence_data[register][row]
                            else:
                                value = _reg[2]
                        else:
                            _reg = register
                            value = _reg[2]
                        value, _fmt = self.__fmt_register(_reg, value)
                        target_bytes.append(struct.pack(self.fmt_mode + _fmt, value))

            for register in self.command[command_name][command_type]:
                if isinstance(register, list):
                    value, _fmt = self.__fmt_register(register, register[2])
                    if _fmt == 'file_data':
                        command.append(value)
                    else:
                        command.append(struct.pack(self.fmt_mode + _fmt, value))
                elif isinstance(register, str):
                    if register == file_context_flag:
                        command.append(file_data)
                    elif register == file_length_flag:
                        command.append(struct.pack(self.fmt_mode + 'I', file_length))
                    elif register in self.param:
                        value, _fmt = self.__fmt_register(self.param[register], self.param[register][2])
                        if _fmt == 'file_data':
                            command.append(value)
                        else:
                            command.append(struct.pack(self.fmt_mode + _fmt, value))
                    elif register == f'{{{{{command_name}}}}}':
                        command.extend(target_bytes)
                    else:
                        logging.warning(msg=f'指令({command_name})的({register})不存在')
                else:
                    logging.warning(msg=f'指令({command_name})的({register})格式不正确')
        except Exception as e:
            logging.error(msg=f'{e},指令转码失败')

        command = b''.join(command)
        assert len(command) >= 16, f'指令({command_name})不正确'
        # self.kit.interface.send_bytes(command[0: 12] + struct.pack(self.fmt_mode + 'I', len(command)) + command[16:])
        return command[0: 12] + struct.pack(self.fmt_mode + 'I', len(command)) + command[16:]

    def __fmt_register(self, register: list, value):
        try:

            if register[1] == "file_data":
                file_data, file_length = self.__get_file(value)
                return file_data, "file_data"
            if register[1] == "file_length":
                file_data, file_length = self.__get_file(value)
                return file_length, 'I'
            if isinstance(value, str) and value.startswith('0x'):
                value = int(value, 16)
            if isinstance(value, str) and value.startswith('0b'):
                value = int(value, 2)
            if len(register) > 3:
                # 发送时做参数计算
                x = value
                value = eval(register[-1])
            fmt_str = value_type[register[1]]
            return value_python[register[1]](value), fmt_str
        except Exception as e:
            logging.error(msg=f'{e},寄存器({register[0]})有误')
        return 0, 'I'

    @staticmethod
    def __get_file(file_name):
        try:
            with open(file_name, 'rb') as fp:
                data = fp.read()
            return data, len(data)
        except Exception as e:
            logging.error(msg=f'{e},文件读取失败')
        return b'', 0

    def execute_icd_command(self, parm_name: str) -> list:
        """!
        @brief 查找指令并执行
        @details 根据参数名查找指令并执行指令
        @param parm_name: 参数名/指令名
        @return 结果列表
        """
        # 筛选所有要发送的指令名
        command_list = []
        if parm_name in self.command:
            command_list.append(parm_name)
        else:
            for command in self.command:
                if parm_name in self.command[command]["send"]:
                    command_list.append(command)

        # 发送
        if self.check_recv_head:
            return self.send_and_check(command_list)
        else:
            return self.send_and_not_check(command_list)

    def send_and_check(self, command_list):
        result_list = []
        for command in command_list:
            if len(self.command[command]["recv"]) < 5:
                # 接收包头, id, 序号, 指令长度, 结果参数
                raise RuntimeError(f"The {command} recv register is not define, or recv register<5.")
            else:
                send_cmd = self.fmt_command(command_name=command, command_type="send")
                recv_cmd = self.fmt_command(command_name=command, command_type="recv")
                total_len = len(send_cmd)
                send_len = self.kit.itf_cmd.send_bytes(send_cmd)
                if total_len != send_len:
                    raise RuntimeError(f"{command} total_len is {total_len}, but just send {send_len}!")
                recv = self.kit.itf_cmd.recv_bytes(struct.unpack("=I", recv_cmd[12:16])[0])
                self.check_recv(recv_cmd, recv, command)
                result_list.append(recv)

                # 写入到参数中
                length = 16
                for index, data in enumerate(self.command[command]["recv"]):
                    if index >= 4:
                        if isinstance(data, list):
                            length += type_size[data[1]]
                        elif isinstance(data, str):
                            data_size = type_size[self.param[data][1]]
                            data_type = value_type[self.param[data][1]]
                            self.set_param(data, struct.unpack(f"={data_type}", recv[length:length+data_size])[0])
                            length += data_size
        return result_list

    def send_and_not_check(self, command_list):
        result_list = []
        for command in command_list:
            send_cmd = self.fmt_command(command_name=command, command_type="send")

            recv_length = 0
            for index, data in enumerate(self.command[command]["recv"]):
                if isinstance(data, list):
                    recv_length += type_size[data[1]]
                elif isinstance(data, str):
                    recv_length += type_size[self.param[data][1]]

            total_len = len(send_cmd)
            send_len = self.kit.itf_cmd.send_bytes(send_cmd)
            if total_len != send_len:
                raise RuntimeError(f"{command} total_len is {total_len}, but just send {send_len}!")

            recv = self.kit.itf_cmd.recv_bytes(recv_length)
            result_list.append(recv)

            length = 0
            for index, data in enumerate(self.command[command]["recv"]):
                if isinstance(data, list):
                    length += type_size[data[1]]
                elif isinstance(data, str):
                    data_size = type_size[self.param[data][1]]
                    data_type = value_type[self.param[data][1]]
                    self.set_param(data, struct.unpack(f"={data_type}", recv[length:length + data_size])[0])
                    length += data_size

        return result_list

    @staticmethod
    def check_recv(recv_cmd, recv, command):
        """!
        @brief 检查返回值
        @details 检查返回指令的包头与icd文件中的是否一样
        @param recv_cmd: icd中对应指令的recv指令
        @param recv: 返回的指令
        @param command: 指令名
        @return
        """
        if recv_cmd[0:4] != recv[0:4]:
            raise RuntimeError(f"The {command} Recv head should be {recv_cmd[0:4].hex()}, recv is {recv[0:4].hex()}")
        if recv_cmd[4:8] != recv[4:8]:
            raise RuntimeError(f"The {command} Recv id should be {recv_cmd[4:8].hex()}, recv is {recv[4:8].hex()}")
        if recv_cmd[8:12] != recv[8:12]:
            raise RuntimeError(f"The {command} Recv num should be {recv_cmd[8:12].hex()}, recv is {recv[8:12].hex()}")

    def param_is_command(self, parm_name: str) -> bool:
        """!
        @brief 参数是不是指令
        @details 判断给出的addr是不是icd指令名
        @param parm_name: 参数名
        @return True/False
        """
        if parm_name in self.command:
            return True
        return False

