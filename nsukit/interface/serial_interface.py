from threading import Lock

import serial

from .base import BaseCmdUItf
from ..tools.logging import logging


class SerialCmdUItf(BaseCmdUItf):
    _target_id = 'COM0'
    _target_baud_rate = 9600
    _timeout = 5

    def __init__(self):
        """
        串口指令收发接口

        """
        self._device_serial = None
        self.busy_lock = Lock()

    def accept(self, target_id=None, target_baud_rate: int = None, **kwargs):
        _target_id = self._target_id if target_id is None else target_id
        _target_baud_rate = self._target_baud_rate if target_baud_rate is None else target_baud_rate
        with self.busy_lock:
            if self._device_serial is not None:
                self._device_serial.close()
            self._device_serial = serial.Serial(port=_target_id,
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
        return self.send_bytes(cmd)

    def read(self, addr: int) -> bytes:
        cmd = self._fmt_reg_read(addr)
        return self.send_bytes(cmd)

    def close(self):
        try:
            self._device_serial.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, value):
        self._device_serial.timeout = value
