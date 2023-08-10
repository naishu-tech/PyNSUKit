import struct
from threading import Lock

import serial

from .base import BaseCmdUItf
from ..tools.logging import logging


def head_check(send_cmd, recv_cmd):
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
    _target = 'COM0'
    _target_baud_rate = 9600
    _timeout = 5

    def __init__(self):
        """
        串口指令收发接口

        """
        self._device_serial = None
        self.busy_lock = Lock()

    def accept(self, target=None, target_baud_rate: int = None, **kwargs):
        _target = self._target if target is None else target
        _target_baud_rate = self._target_baud_rate if target_baud_rate is None else target_baud_rate
        with self.busy_lock:
            if self._device_serial is not None:
                self._device_serial.close()
            self._device_serial = serial.Serial(port=_target,
                                                baudrate=int(_target_baud_rate),
                                                timeout=self._timeout)

    def recv_bytes(self, size: int = 1024) -> bytes:
        """

        @param size:
        @return:
        """
        with self.busy_lock:
            return self._device_serial.read(size)

    def send_bytes(self, data: bytes):
        with self.busy_lock:
            return self._device_serial.write(data)

    def write(self, addr: int, value: int) -> int:
        cmd = self._fmt_reg_write(addr, value)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        return int.from_bytes(result, "little")

    def read(self, addr: int) -> int:
        cmd = self._fmt_reg_read(addr)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        return int.from_bytes(result, "little")

    def close(self):
        try:
            self._device_serial.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, value):
        self._device_serial.timeout = value
