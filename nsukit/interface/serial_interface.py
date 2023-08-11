import struct
from threading import Lock

import serial

from .base import BaseCmdUItf
from ..tools.logging import logging


def head_check(send_cmd, recv_cmd):
    """!
    @brief 包头检查
    @details 返回数据包头检查
    @param send_cmd 发送的指令
    @param recv_cmd 返回的指令
    @return 返回指令的总长度
    """
    send_head = struct.unpack('=IIII', send_cmd[0:16])
    recv_head = struct.unpack('=IIII', recv_cmd)
    if recv_head[0] != 0xCFCFCFCF:
        raise RuntimeError("返回包头错误")
    if recv_head[1] != send_head[1]:
        raise RuntimeError("返回ID错误")
    if recv_head[2] != send_head[2]:
        raise RuntimeError("返回序号错误")
    return recv_head[3]


class SerialCmdUItf(BaseCmdUItf):
    """!
    @brief 串口指令接口
    @details 包括连接/断开、发送、接收等功能
    """
    _target = 'COM0'
    _target_baud_rate = 9600
    _timeout = 5

    def __init__(self):
        self._device_serial = None
        self.busy_lock = Lock()

    def accept(self, target=None, target_baud_rate: int = None, **kwargs):
        """!
        @brief 初始化串口指令接口
        @details 初始化串口指令接口，获取串口id，波特率等参数
        @param target 串口id
        @param target_baud_rate 波特率
        @param kwargs 其他参数
        @return
        """
        _target = self._target if target is None else target
        _target_baud_rate = self._target_baud_rate if target_baud_rate is None else target_baud_rate
        with self.busy_lock:
            if self._device_serial is not None:
                self._device_serial.close()
            self._device_serial = serial.Serial(port=_target,
                                                baudrate=int(_target_baud_rate),
                                                timeout=self._timeout)

    def recv_bytes(self, size: int = 1024) -> bytes:
        """!
        @brief 接收数据
        @details 使用串口接收指定大小的数据
        @param size 接收数据的长度
        @return 接收到的数据
        """
        with self.busy_lock:
            return self._device_serial.read(size)

    def send_bytes(self, data: bytes):
        """!
        @brief 发送数据
        @details 使用串口发送数据
        @param data 要发送的数据
        @return 发送完成的数据长度
        """
        with self.busy_lock:
            return self._device_serial.write(data)

    def write(self, addr: int, value: int) -> int:
        """!
        @brief 发送数据
        @details 使用串口以地址值的方式发送一条约定好的特殊指令
        @param addr 要修改的地址
        @param value 地址中要赋的值
        @return 返回数据中的结果
        """
        cmd = self._fmt_reg_write(addr, value)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        return int.from_bytes(result, "little")

    def read(self, addr: int) -> int:
        """!
        @brief 接收数据
        @details 使用串口以地址的方式发送一条约定好的特殊指令
        @param addr 要读取的地址
        @return 返回读取到的结果
        """
        cmd = self._fmt_reg_read(addr)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        return int.from_bytes(result, "little")

    def close(self):
        """!
        @brief 关闭连接
        @details 关闭串口连接
        @return
        """
        try:
            self._device_serial.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, value):
        """!
        @brief 设置超时时间
        @details 根据传入的数值设置串口的超时时间
        @param value 秒
        @return
        """
        self._device_serial.timeout = value
