# Copyright (c) [2023] [NaiShu]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import struct
import math
from typing import List, Iterable, Union, Callable, Any
from dataclasses import dataclass

import numpy as np

from ..tools.check_func import head_check


@dataclass
class InitParamSet:
    cmd_ip: str = ''
    cmd_tcp_port: int = 5001

    cmd_serial_port: str = ''
    cmd_baud_rate: int = -1

    cmd_board: int = -1
    cmd_sent_base: int = 0
    cmd_recv_base: int = 0
    cmd_irq_base: int = 0
    cmd_sent_down_base: int = 0

    stream_ip: str = ''
    stream_tcp_port: int = 0

    stream_board: int = 0

    # ICDMw所需参数
    icd_path: str = None
    check_recv_head: bool = True

    stream_mode: str = 'real'


class UInterfaceMeta(type):
    """!
    @note 协议层接口的元类，当前做类型注解用，开发协议层接口时不用关心此类
    """
    ...


class UInterface(metaclass=UInterfaceMeta):
    def accept(self, param: InitParamSet) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.accept.__name__} method')

    def close(self) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.close.__name__} method')

    def set_timeout(self, s: float) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.set_timeout.__name__} method')


class RegOperationMixin:
    """!

    """
    def reg_write(self, addr, value) -> bool:
        ...

    def reg_read(self, addr) -> int:
        ...


class BaseCmdUItf(UInterface):
    def send_bytes(self, data: bytes) -> int:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.send_bytes.__name__} method')

    def recv_bytes(self, size: int) -> bytes:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.recv_bytes.__name__} method')

    def send_down(self):
        ...

    def recv_down(self):
        ...

    def write(self, addr: int, value: bytes) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.write.__name__} method')

    def read(self, addr: int) -> bytes:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.read.__name__} method')

    def multi_write(self, addr: Iterable[int], value: Iterable[bytes]) -> None:
        """!

        @param addr:
        @param value:
        @return:
        """
        for _a, _v in zip(addr, value):
            self.write(_a, _v)

    def multi_read(self, addr: Iterable[int]) -> Iterable[bytes]:
        """!

        @param addr:
        @return:
        """
        res = []
        for _a in addr:
            res.append(self.read(_a))
        return res

    def increment_write(self, addr: int, value: bytes, reg_len: int = 4) -> None:
        """!
        从一个基地址开始，将value的内容依次写入后续寄存器
        @param addr: 基地址
        @param value: 不定长的待写入数
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        length = len(value)
        num = length // reg_len
        for _n in range(num):
            self.write(addr+reg_len*_n, value[_n:_n*reg_len])
        if (length - num*reg_len) > 0:
            _data = value[num:]
            _data += b'\x00'*(reg_len-len(_data))
            self.write(addr+reg_len*num, _data)

    def increment_read(self, addr: int, length: int, reg_len: int = 4) -> bytes:
        """!
        从一个基地址开始，将value的内容依次写入后续寄存器
        @param addr: 基地址
        @param length: 要读取的数据长度
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        cache = []
        ceil_len = math.ceil(length/reg_len)*reg_len
        num = ceil_len//reg_len
        for _n in range(num):
            cache.append(self.read(addr+reg_len*_n))
        return b''.join(cache)[:length]

    def loop_write(self, addr: int, value: bytes, reg_len: int = 4) -> None:
        """!
        向给定地址addr，将value的内容依次写入后续寄存器
        @param addr: 基地址
        @param value: 不定长的待写入数
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        length = len(value)
        num = length // reg_len
        for _n in range(num):
            self.write(addr, value[_n:_n * reg_len])
        if length - num * reg_len > 0:
            _data = value[num:]
            _data += b'\x00' * (reg_len - len(_data))
            self.write(addr, _data)

    def loop_read(self, addr: int, length: int, reg_len: int = 4) -> bytes:
        """!
        在一个寄存器地址上，依次读出指定长度的数据
        @param addr: 基地址
        @param length: 要读取的数据长度
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        cache = []
        ceil_len = math.ceil(length/reg_len)*length
        num = ceil_len//reg_len
        for _n in range(num):
            cache.append(self.read(addr))
        return b''.join(cache)[:length]


class VirtualRegCmdMixin:
    """!
    @brief BaseCmdUItf类的Mixin，针对原生不支持寄存器方式的物理协议接口类

    1. 封装了模拟寄存器读写的几条ICD
    2. 继承后会重载
        1. [BaseCmdUItf.increment_write](#nsukit.interface.base.BaseCmdUItf.increment_write)
        2. [BaseCmdUItf.increment_read](#nsukit.interface.base.BaseCmdUItf.increment_read)
        3. [BaseCmdUItf.loop_write](#nsukit.interface.base.BaseCmdUItf.loop_write)
        4. [BaseCmdUItf.loop_read](#nsukit.interface.base.BaseCmdUItf.loop_read)
        5. [BaseCmdUItf.multi_write](#nsukit.interface.base.BaseCmdUItf.multi_write)
        6. [BaseCmdUItf.multi_read](#nsukit.interface.base.BaseCmdUItf.multi_read)

    3. 使用方式
    @code
    >>> class ExampleUItf(VirtualRegCmdMixin, BaseCmdUItf):
    >>>    ...
    """
    @staticmethod
    def _fmt_reg_write(reg: int = 0, value: bytes = b'') -> bytes:
        """!
        @brief 格式化TCP/serial模拟写寄存器功能的icd
        @param reg: 寄存器地址
        @param value: 寄存器值
        @return 格式化好的icd指令
        """
        if not isinstance(value, bytes):
            raise RuntimeError("The value can't be pack")
        pack = (0x5F5F5F5F, 0x31001000, 0x00000000, 24, reg)
        send_cmd = struct.pack('=IIIII', *pack)
        send_cmd += value
        return send_cmd

    @staticmethod
    def _fmt_reg_read(reg: int = 0) -> bytes:
        """!
        @brief 格式化TCP/serial模拟读寄存器功能的icd
        @param reg: 寄存器地址
        @return 格式化好的icd指令
        """
        pack = (0x5F5F5F5F, 0x31001001, 0x00000000, 20, reg)
        return struct.pack('=IIIII', *pack)

    def _common_write(self: Union[BaseCmdUItf, "VirtualRegCmdMixin"], addr: int, value: bytes, board: Any) -> None:
        """!
        @brief 通用的写寄存器方法
        @details 以地址值的方式发送一条约定好的特殊指令
        @param addr 要修改的地址
        @param value 地址中要赋的值
        @return 无
        """
        cmd = self._fmt_reg_write(addr, value)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        self.send_down()
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        self.recv_down()
        if struct.unpack('=I', result)[0] != 0:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to write to register {hex(addr)} on board {board}')

    def _common_read(self: Union[BaseCmdUItf, "VirtualRegCmdMixin"], addr: int, board: Any) -> bytes:
        """!
        @brief 通用的读寄存器方法
        @details 以地址值的方式发送一条约定好的特殊指令
        @param addr 要读取的地址
        @return 返回读取到的结果
        """
        cmd = self._fmt_reg_read(addr)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        self.send_down()
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        self.recv_down()
        if struct.unpack('=I', result[:4])[0] != 0:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to read to register {hex(addr)} on board {board}')
        return result[4:]

    def multi_write(self: BaseCmdUItf, addr: Iterable[int], value: Iterable[bytes]) -> None:
        """!
        重载：[BaseCmdUItf.multi_write](#nsukit.interface.base.BaseCmdUItf.multi_write)
        @param addr:
        @param value:
        @return:
        """
        return BaseCmdUItf.multi_write(self, addr, value)

    def multi_read(self: BaseCmdUItf, addr: Iterable[int]) -> Iterable[bytes]:
        """!
        重载：[BaseCmdUItf.multi_read](#nsukit.interface.base.BaseCmdUItf.multi_read)
        @param addr:
        @return:
        """
        return BaseCmdUItf.multi_read(self, addr)

    def increment_write(self: BaseCmdUItf, addr: int, value: bytes, reg_len: int = 4) -> None:
        """!
        从一个基地址开始，将value的内容依次写入后续寄存器

        重载：[BaseCmdUItf.increment_write](#nsukit.interface.base.BaseCmdUItf.increment_write)
        @param addr: 基地址
        @param value: 不定长的待写入数
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        length = len(value)
        padding_len = int(math.ceil(length/reg_len)*reg_len)
        padding = b'/x00'*(padding_len-length)
        pack = (0x5F5F5F5F, 0x31001010, 0x00000000, padding_len+6*4, addr, padding_len)
        head = struct.pack('=IIIIII', *pack)
        cmd = b''.join((head, value, padding))   # 格式化完成指令
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        self.send_down()
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        self.recv_down()
        if struct.unpack('=I', result) != 0:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to increment_write to base register {hex(addr)}')

    def increment_read(self: BaseCmdUItf, addr: int, length: int, reg_len: int = 4) -> bytes:
        """!
        从一个基地址开始，将value的内容依次写入后续寄存器

        重载：[BaseCmdUItf.increment_read](#nsukit.interface.base.BaseCmdUItf.increment_read)
        @param addr: 基地址
        @param length: 要读取的数据长度
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        padding_len = int(math.ceil(length / reg_len) * reg_len)
        pack = (0x5F5F5F5F, 0x31001011, 0x00000000, 24, addr, padding_len)
        cmd = struct.pack('=IIIIII', *pack)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        self.send_down()
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        self.recv_down()
        if struct.unpack('=I', result[:4]) != 0:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to increment_write to base register {hex(addr)}')
        return result[4:length+4]

    def loop_write(self: BaseCmdUItf, addr: int, value: bytes, reg_len: int = 4) -> None:
        """!
        向给定地址addr，将value的内容依次写入后续寄存器

        重载：[BaseCmdUItf.loop_write](#nsukit.interface.base.BaseCmdUItf.loop_write)
        @param addr: 基地址
        @param value: 不定长的待写入数
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        length = len(value)
        padding_len = int(math.ceil(length / reg_len) * reg_len)
        padding = b'/x00' * (padding_len - length)
        pack = (0x5F5F5F5F, 0x31001020, 0x00000000, padding_len + 6 * 4, addr, padding_len)
        head = struct.pack('=IIIIII', *pack)
        cmd = b''.join((head, value, padding))  # 格式化完成指令
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        self.send_down()
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        self.recv_down()
        if struct.unpack('=I', result) != 0:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to increment_write to base register {hex(addr)}')

    def loop_read(self: BaseCmdUItf, addr: int, length: int, reg_len: int = 4) -> bytes:
        """!
        在一个寄存器地址上，依次读出指定长度的数据

        重载：[BaseCmdUItf.loop_read](#nsukit.interface.base.BaseCmdUItf.loop_read)
        @param addr: 基地址
        @param length: 要读取的数据长度
        @param reg_len: 单个寄存器的长度
        @return 无返回值
        """
        padding_len = int(math.ceil(length / reg_len) * reg_len)
        pack = (0x5F5F5F5F, 0x31001021, 0x00000000, 24, addr, padding_len)
        cmd = struct.pack('=IIIIII', *pack)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        self.send_down()
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        self.recv_down()
        if struct.unpack('=I', result[:4]) != 0:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to increment_write to base register {hex(addr)}')
        return result[4:length + 4]


class BaseStreamUItf(UInterface):
    def alloc_buffer(self, length: int, buf: Union[int, np.ndarray, None] = None) -> int:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.alloc_buffer.__name__} method')

    def free_buffer(self, fd: int) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.free_buffer.__name__} method')

    def get_buffer(self, fd: int, length: int) -> np.ndarray:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.get_buffer.__name__} method')

    def open_send(self, chnl: int, fd: int, length: int, offset: int = 0) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.open_send.__name__} method')

    def open_recv(self, chnl: int, fd: int, length: int, offset: int = 0) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.open_recv.__name__} method')

    def wait_stream(self, fd: int, timeout: float = 0.) -> int:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.wait_stream.__name__} method')

    def break_stream(self, fd: int) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.break_stream.__name__} method')

    def stream_recv(self, chnl: int, fd: int, length: int, offset: int = 0,
                    stop_event: Callable = None, time_out: float = 0xFFFFFFFF, flag: int = 1) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.stream_recv.__name__} method')

    def stream_send(self, chnl: int, fd: int, length: int, offset: int = 0,
                    stop_event: Callable = None, time_out: float = 0xFFFFFFFF, flag: int = 1) -> None:
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.stream_send.__name__} method')
