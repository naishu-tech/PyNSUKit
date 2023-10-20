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
from threading import Lock

import serial

from .base import BaseCmdUItf, VirtualRegCmdMixin, BaseStreamUItf, InitParamSet
from ..tools.logging import logging
from ..tools.check_func import head_check


class SerialCmdUItf(VirtualRegCmdMixin, BaseCmdUItf):
    """!
    @brief 串口指令接口
    @details 包括连接/断开、发送、接收等功能
    @image html professional_serial_cmd.png
    """
    _target = 'COM0'
    _target_baud_rate = 9600
    _timeout = 15

    def __init__(self):
        self.serial_port = self._target
        self.baud_rate = self._target_baud_rate
        self._device_serial = None
        self.busy_lock = Lock()

    def accept(self, param: InitParamSet) -> None:
        """!
        @brief 初始化串口指令接口
        @details 初始化串口指令接口，获取串口id，波特率等参数
        @param param InitParamSet或其子类的对象，需包含cmd_serial_port、cmd_baud_rate属性
        @return
        """
        _target = self.serial_port if param.cmd_serial_port is None else param.cmd_serial_port
        _target_baud_rate = self.baud_rate if param.cmd_baud_rate is None else param.cmd_baud_rate
        with self.busy_lock:
            if self._device_serial is not None:
                self._device_serial.close()
            self._device_serial = serial.Serial(port=_target,
                                                baudrate=int(_target_baud_rate),
                                                timeout=self._timeout)
            self.serial_port = _target
            self.baud_rate = _target_baud_rate

    def recv_bytes(self, size) -> bytes:
        """!
        @brief 接收数据
        @details 使用串口接收指定大小的数据
        @param size 接收数据的长度
        @return 接收到的数据
        """
        with self.busy_lock:
            recv_data = b''
            recv_size = 0
            while True:
                if recv_size != size:
                    data = self._device_serial.read(size)
                    recv_data += data
                    recv_size += len(data)
                if recv_size >= size:
                    break
            return recv_data

    def send_bytes(self, data: bytes) -> int:
        """!
        @brief       发送数据
        @details     使用串口发送数据
        @param data  要发送的数据
        @return      发送完成的数据长度
        """
        with self.busy_lock:
            total_len = len(data)
            total_sendlen = 0
            while True:
                send_len = self._device_serial.write(data[total_sendlen:])
                total_sendlen += send_len
                if total_len == total_sendlen:
                    return total_len
                if send_len == 0:
                    raise RuntimeError("Connection interruption")

    def write(self, addr: int, value: bytes) -> None:
        """!
        @brief 以串口进行写寄存器
        @param addr 要修改的地址
        @param value 地址中要赋的值
        @return 无
        """
        return self._common_write(addr, value, self.serial_port)

    def read(self, addr: int) -> bytes:
        """!
        @brief 接收数据
        @details 使用串口以地址的方式发送一条约定好的特殊指令
        @param addr 要读取的地址
        @return 返回读取到的结果
        """
        return self._common_read(addr, self.serial_port)

    def close(self) -> None:
        """!
        @brief 关闭连接
        @details 关闭串口连接
        @return
        """
        try:
            self._device_serial.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, s: float) -> None:
        """!
        @brief 设置超时时间
        @details 根据传入的数值设置串口的超时时间
        @param s 秒
        @return
        """
        self._device_serial.timeout = s


class SerialStreamUItf(BaseStreamUItf):
    """!
    @todo SerialStreamUItf接口待开发，暂不支持串口数据流
    """
    ...
