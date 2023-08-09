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
    "file": str
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
    fmt_mode = "="  # pack/unpack 大小端模式

    def __init__(self, kit: "NSUKit", file_name='icd.json'):
        super(ICDRegMw, self).__init__(kit)
        self._file_name = file_name
        self.icd_data = {}
        self.param = {}
        self.command_send = {}
        self.command_recv = {}
        self.sequence = {}

    def config(self, *, icd_path=None, **kwargs):
        """!
        指定icd配置文件的路径
        @param icd_path:
        @param kwargs:
        @return:
        """
        if icd_path is None:
            icd_path = nsukit.__file__
            icd_path = icd_path.replace('__init__.py', 'icd.json')
        self._file_name = icd_path
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
                logging.error(msg=f'{e}, {self._file_name} 不可用')
                return False
        try:
            # 从 'icd_data' 字典中提取特定数据并将其设置为实例变量
            self.param = self.icd_data['param']
            self.command_send = self.icd_data['command_send']
            self.command_recv = self.icd_data['command_recv']
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
        # TODO: ICD的保存怎么在nsukit中引出
        path = path + '\\' if path else path
        with open(path + self._file_name.split('.')[0] + '_run.json', 'w', encoding='utf-8') as fp:
            # 按utf-8的格式格式化并写入文件
            json.dump(self.icd_data, fp, ensure_ascii=False, indent=4)
            logging.info(msg='参数保存成功')
        return True

    def get_param(self, param_name: str, default=0, fmt_type=int):
        param = self.param.get(param_name, None)
        if param is None:
            logging.warning(msg=f'未找到参数：{param_name}')
            self.param.update({param_name: [param_name, 'uint32', default]})
            return fmt_type(default)
        return fmt_type(param[2])

    def set_param(self, param_name: str, value, fmt_type=int):
        param = self.param.get(param_name, [param_name, 'uint32', value])
        if isinstance(value, str) and value.startswith('0x'):
            param[2] = int(value, 16)
        elif isinstance(value, str) and value.startswith('0b'):
            param[2] = int(value, 2)
        elif isinstance(value, str) and '.' in value and param[1] != 'file':
            param[2] = float(value)
        else:
            param[2] = value_python[param[1]](value)
        self.param.update({param_name: param})

    def fmt_command(self, command_name, file_name=None) -> bytes:
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

            for register in self.command_send[command_name]:
                if isinstance(register, list):
                    value, _fmt = self.__fmt_register(register, register[2])
                    command.append(struct.pack(self.fmt_mode + _fmt, value))
                elif isinstance(register, str):
                    if register == file_context_flag:
                        command.append(file_data)
                    elif register == file_length_flag:
                        command.append(struct.pack(self.fmt_mode + 'I', file_length))
                    elif register in self.param:
                        value, _fmt = self.__fmt_register(self.param[register], self.param[register][2])
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

    @staticmethod
    def __fmt_register(register: list, value):
        try:
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

    def find_command(self, parm_name: str) -> list:
        """!
        根据参数名称,查找所有包含此参数的指令名

        @param parm_name: 参数名
        @return 包含此参数的的指令集合 list

        """
        send_len = []
        for command in self.command_send:
            if parm_name in self.command_send[command]:
                send_len.append(self.kit.itf_cmd.send_bytes(self.fmt_command(command)))
        return send_len
