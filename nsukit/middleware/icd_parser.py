# Copyright (c) [2023] [NaiShu]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import json
import struct
from typing import TYPE_CHECKING, Optional

try:
    import numpy as np
    EnableNumpy = True
except ImportError as e:
    EnableNumpy = False

import nsukit
from .base import BaseRegMw
from ..interface.base import InitParamSet
from ..tools.logging import logging

if TYPE_CHECKING:
    from .. import NSUSoc

file_context_flag = '__file__'
file_length_flag = '__filelength__'
array_context_flag = '__array__'
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
    @details 用于使用icd进行指令收发，关于ICD的定义可查看 @ref md_ICD文件格式
    @image html icd_sch_packinfo.png
    """
    fmt_mode = "="   # pack/unpack 大小端模式
    FPack_TIdx = 0  # fpack格式中type描述的索引号
    FPack_VIdx = 1  # fpack格式中value描述的索引号

    def __init__(self, kit: "NSUSoc", file_name='icd.json'):
        super(ICDRegMw, self).__init__(kit)
        self._file_name = file_name
        self.icd_data = {}
        self.param = {}
        self.command = {}
        self.sequence = {}
        self.check_recv_head = False

    def config(self, param: InitParamSet) -> None:
        """!
        @brief 配置icd路径
        @details 指定icd配置文件的路径，并加载icd
        @param param:
        @return:
        """
        if param.icd_path is None:
            icd_path = nsukit.__file__
            icd_path = icd_path.replace('__init__.py', 'icd.json')
        else:
            icd_path = param.icd_path
        self._file_name = icd_path
        self.check_recv_head = param.check_recv_head
        self.load()

    def load(self):
        """!
        从文件中加载数据，并相应地设置实例变量。
        此方法从指定的文件中读取数据，通常文件采用JSON格式存储，并将读取的数据设置为相关实例变量。
        文件中包含了与接口控制文档 (ICD) 相关的信息。

        @return: 若数据成功加载，则返回True；否则返回False。
        @rtype: bool
        """
        file_path = self._file_name
        # 使用utf-8编码打开文件并以读取模式
        with open(file_path, 'r', encoding='utf-8') as fp:
            try:
                # 尝试将JSON数据从文件加载到 'icd_data' 实例变量中
                self.icd_data = json.load(fp)
            except json.decoder.JSONDecodeError as e:
                # 如果出现JSON解码错误，记录错误消息并返回False表示加载失败
                logging.error(msg=f'{e}, {self._file_name} unavailable')
                return False
        try:
            # 从 'icd_data' 字典中提取特定数据并将其设置为实例变量
            self.param = self.icd_data['param']
            self.command = self.icd_data['command']
            self.sequence = self.icd_data['sequence']
            # 记录成功消息，表示ICD参数加载成功
            logging.info(msg='ICD Parameters loaded successfully')
        except Exception as e:
            # 如果提取数据或设置实例变量时出现异常，记录错误并返回False
            logging.error(msg=f'{e}, {file_path} unavailable')
            return False
        # 返回True，表示数据加载成功
        return True

    def save(self, path=''):
        """!
        @brief 保存icd
        @details 将当前运行icd参数以另一个名称进行保存
        @todo ICD的保存怎么在nsukit中引出待开发
        @param path: 文件路径
        @return: True
        """
        path = path + '\\' if path else path
        with open(path + self._file_name.split('.')[0] + '_run.json', 'w', encoding='utf-8') as fp:
            # 按utf-8的格式格式化并写入文件
            json.dump(self.icd_data, fp, ensure_ascii=False, indent=4)
            logging.info(msg='参数保存成功')
        return True

    def get_param(self, param_name: str, default=0):
        """!
        @brief 获取icd参数
        @details 根据参数名称获取参数值
        @param param_name: 参数名称
        @param default: 默认值
        @param fmt_type: 参数值格式化类型
        @return: 格式化后的参数值
        """
        v_idx = self.FPack_VIdx
        t_idx = self.FPack_TIdx
        param = self.param.get(param_name, None)
        if isinstance(param[v_idx], str) and param[v_idx].startswith('0x'):
            return int(param[v_idx], 16)
        elif isinstance(param[v_idx], str) and param[v_idx].startswith('0b'):
            return int(param[v_idx], 2)
        elif param[t_idx] == "file" or param[t_idx] == "file_length":
            return param[v_idx]
        elif param is None:
            logging.warning(msg=f'未找到参数：{param_name}')
            self.param.update({param_name: ['uint32', default]})
            return int(default)
        return value_python[param[t_idx]](param[v_idx])

    def set_param(self, param_name: str, value):
        """!
        @brief 设置参数值
        @details 根据参数名称设置相应的值
        @param param_name: 参数名称
        @param value: 参数值
        @param fmt_type: 参数值格式化类型
        @return:
        """
        v_idx = self.FPack_VIdx
        t_idx = self.FPack_TIdx
        if v_idx == 1:
            param = self.param.get(param_name, ['uint32', value])
        elif v_idx == 2:
            param = self.param.get(param_name, ['', 'uint32', value])
        else:
            raise RuntimeError(f'The value of class attribute fpack_v_idx should not be {v_idx}')

        if isinstance(value, str) and value.startswith('0x'):
            param[v_idx] = int(value, 16)
        elif isinstance(value, str) and value.startswith('0b'):
            param[v_idx] = int(value, 2)
        elif param[t_idx] == "file" or param[t_idx] == "file_length":
            param[v_idx] = value
        elif isinstance(value, str) and '.' in value and param[t_idx] != 'file':
            param[v_idx] = float(value)
        else:
            param[v_idx] = value_python[param[t_idx]](value)
        self.param.update({param_name: param})

    def fmt_command(self, command_name, command_type: Optional[str] = "send", file_name=None, arrays=None) -> bytes:
        """!
        @brief 格式化指令
        @details 根据指令名、指令类型和文件名组合成指令
        @param command_name: 指令名称
        @param command_type: 指令类型(发送接收)
        @param file_name: 文件名
        @param arrays: 数组
        @return: 格式化好的指令
        """
        v_idx = self.FPack_VIdx
        file_data = b''
        command = []
        __array__ = []
        file_length = 0
        if arrays is not None and not EnableNumpy:
            raise ValueError(f'This function relies on numpy but cannot currently be imported')
        if isinstance(file_name, str):
            file_data, file_length = self.__get_file(file_name)
        elif isinstance(file_name, np.ndarray):
            file_data = file_name.tobytes()
        if isinstance(arrays, np.ndarray):
            __array__ = [array.tobytes() for array in arrays]
        try:
            target_bytes = []
            if command_name in self.sequence:
                raise ValueError(f'Sequence mode is not supported temporarily')

            cpack = self.command[command_name] if command_type is None else self.command[command_name][command_type]
            for register in cpack:
                if isinstance(register, list):
                    value, _fmt = self.__fmt_register(register, register[v_idx])
                    if _fmt == 'file':
                        command.append(value)
                    else:
                        command.append(struct.pack(self.fmt_mode + _fmt, value))
                elif isinstance(register, str):
                    if register == file_context_flag:
                        command.append(file_data)
                    elif register == file_length_flag:
                        command.append(struct.pack(self.fmt_mode + 'I', file_length))
                    elif register.startswith(array_context_flag):
                        command.append(eval(register))
                    elif register in self.param:
                        value, _fmt = self.__fmt_register(self.param[register], self.param[register][value])
                        if _fmt == 'file':
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
        return b''.join((command[0: 12], struct.pack(self.fmt_mode + 'I', len(command)), command[16:]))

    def __fmt_register(self, register: list, value):
        t_idx = self.FPack_TIdx
        try:
            if register[t_idx] == "file":
                file_data, file_length = self.__get_file(value)
                return file_data, "file_data"
            if register[t_idx] == "file_length":
                file_data, file_length = self.__get_file(value)
                return file_length, 'I'
            if isinstance(value, str) and value.startswith('0x'):
                value = int(value, 16)
            if isinstance(value, str) and value.startswith('0b'):
                value = int(value, 2)
            if len(register) > 2:
                # 发送时做参数计算
                x = value
                value = eval(register[-1])
            fmt_str = value_type[register[t_idx]]
            return value_python[register[t_idx]](value), fmt_str
        except Exception as e:
            logging.error(msg=f'{e},寄存器({register[t_idx]})有误')
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

    def execute(self, cname: str, array=None) -> None:
        """!
        执行指令
        @param cname: 指令名称
        @param array: 传入要发送的数组
        @return None
        """
        if cname not in self.command:
            raise ValueError(
                f'Unsupported command {cname}. The current list of available commands includes: {self.command.keys()}')
        if self.check_recv_head:
            return self.send_and_check(cname, array=array)
        else:
            return self.send_and_not_check(cname, array=array)

    def execute_from_pname(self, parm_name: str):
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
        for cmd in command_list:
            self.execute(cmd)

    def send_and_check(self, cname, array=None):
        if len(self.command[cname]["recv"]) < 5:
            # 接收包头, id, 序号, 指令长度, 结果参数
            raise RuntimeError(f"The {cname} recv register is not define, or recv register<5.")
        else:
            send_cmd = self.fmt_command(command_name=cname, command_type="send", arrays=array)
            recv_cmd = self.fmt_command(command_name=cname, command_type="recv")
            total_len = len(send_cmd)
            send_len = self.kit.itf_cs.send_bytes(send_cmd)
            if total_len != send_len:
                raise RuntimeError(f"{cname} total_len is {total_len}, but just send {send_len}!")
            recv = self.kit.itf_cs.recv_bytes(struct.unpack("=I", recv_cmd[12:16])[0])
            self.check_recv(recv_cmd, recv, cname)
            self.enable_param(cname, recv)

    def send_and_not_check(self, cname, array=None):
        t_idx = self.FPack_TIdx
        send_cmd = self.fmt_command(command_name=cname, command_type="send", arrays=array)
        recv_length = 0
        for index, fpack in enumerate(self.command[cname]["recv"]):
            if isinstance(fpack, list):
                recv_length += type_size[fpack[t_idx]]
            elif isinstance(fpack, str):
                recv_length += type_size[self.param[fpack][t_idx]]
        total_len = len(send_cmd)
        send_len = self.kit.itf_cs.send_bytes(send_cmd)
        if total_len != send_len:
            raise RuntimeError(f"{cname} total_len is {total_len}, but just send {send_len}!")
        recv = self.kit.itf_cs.recv_bytes(recv_length)
        self.enable_param(cname, recv)

    def enable_param(self, cname: str, recv: bytes):
        """!
        将接收到的反馈，按recv字段解析并将解析值填入参数
        @param cname: 指令名
        @param recv: 接收到的反馈数据
        @return 无
        """
        t_idx = self.FPack_TIdx
        length = 0
        for index, fpack in enumerate(self.command[cname]["recv"]):
            if isinstance(fpack, list):
                length += type_size[fpack[t_idx]]
            elif isinstance(fpack, str):
                data_size = type_size[self.param[fpack][t_idx]]
                data_type = value_type[self.param[fpack][t_idx]]
                self.set_param(fpack, struct.unpack(f"={data_type}", recv[length:length + data_size])[0])
                length += data_size

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
