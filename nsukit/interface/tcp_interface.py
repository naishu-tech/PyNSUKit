import socket
import threading
import ctypes
from threading import Lock, Event
from dataclasses import dataclass
from typing import Union

import numpy as np

from .base import BaseCmdUItf, BaseChnlUItf
from ..tools.logging import logging


class TCPCmdUItf(BaseCmdUItf):
    _local_port = 5000
    _remote_port = 5001
    _target_id = "127.0.0.1"
    _serial_num = 1
    _timeout = 5

    def __init__(self):
        self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.set_timeout(self._timeout)
        self._recv_addr = (self._target_id, self._remote_port)
        self.busy_lock = Lock()

    def accept(self, target_id=None, *args):
        """

        @param target_id: IP地址
        @param args:
        @return:
        """
        _target_id = self._target_id if target_id is None else target_id
        with self.busy_lock:
            self.close()
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_timeout(self._timeout)
            self._recv_addr = (self._target_id, self._remote_port)
            if args:
                self._tcp_server.connect((_target_id, *args))
            else:
                self._tcp_server.connect((_target_id, self._remote_port))
        self._recv_addr = (_target_id, self._remote_port)

    def recv_bytes(self, size: int = 1024) -> bytes:
        """

        @param size: 返回长度
        @return:
        """
        with self.busy_lock:
            return self._tcp_server.recv(size)

    def send_bytes(self, data: bytes) -> int:
        """

        @param data: 数据
        @return: 已发送的长度
        """
        with self.busy_lock:
            send_len = self._tcp_server.send(data)
            return send_len

    def write(self, addr: int, value: int) -> int:
        cmd = self._fmt_reg_write(addr, value)
        return self.send_bytes(cmd)

    def read(self, addr: int) -> int:
        cmd = self._fmt_reg_read(addr)
        return self.send_bytes(cmd)

    def close(self):
        try:
            self._tcp_server.shutdown(socket.SHUT_RDWR)
            self._tcp_server.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, s: int = 5):
        """

        @param s: 时间（秒）
        @return:
        """
        self._tcp_server.settimeout(s)

    def get_number(self):
        return self._serial_num

    def update_number(self):
        self._serial_num += 1


class TCPChnlUItf(BaseChnlUItf):
    _local_port = 6001
    _timeout = None
    DISCONNECT = 0

    @dataclass
    class Memory:
        memory: np.ndarray
        size: int
        idx: int
        in_use: bool

    def __init__(self):
        """
        网络数据上下行接口

        """
        self.fd = None
        self.stop_event: Union[None, Event] = threading.Event()
        self._tcp_server = None
        self._recv_server = None
        self._recv_addr = None
        self.memory_dict = {}
        self.memory_index = 0
        self.open_flag = False

    def accept(self, port: int = None):
        if not self.open_flag:
            self._local_port = self._local_port if port is None else port
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._tcp_server.bind(('0.0.0.0', self._local_port))
            self._tcp_server.listen(1)
            self.set_timeout(self._timeout)
            self.open_board()
            logging.info(msg='TCP connection established')
            self.open_flag = True

    def recv_bytes(self, size=1024):
        fd = self._recv_server.recv(size, socket.MSG_WAITALL)
        if len(fd) < size:
            return self.DISCONNECT
        fd = np.frombuffer(fd, dtype='u4')
        return fd

    def set_timeout(self, value=2):
        self._tcp_server.settimeout(value)

    def open_board(self):
        if not self.open_flag:
            self._recv_server, self._recv_addr = self._tcp_server.accept()

    def close_board(self):
        if self.open_flag:
            try:
                self._recv_server.shutdown(socket.SHUT_RDWR)
                self._recv_server.close()
            except Exception as e:
                logging.error(msg=e)

    def alloc_buffer(self, length: int, buf: Union[int, np.ndarray, None] = None) -> int:
        """!
        申请内存
        @param length: 内存大小，单位为4Byte
        @param buf: 指定一片内存，buf可为内存指针或np.ndarray
        @return: 内存描述对象的id
        """
        # 输入buf为内存指针时
        if isinstance(buf, int):
            _memory = np.frombuffer((ctypes.c_uint * length).from_address(buf), dtype='u4')
        # 输入buf为numpy.ndarray时
        elif isinstance(buf, np.ndarray):
            _memory = np.frombuffer(buf, dtype='u4')
        else:
            _memory = np.zeros(shape=length, dtype='u4')
        # 截取所需的内存大小
        if _memory.size < length:
            raise ValueError(f'The memory size of the input buf is less than length')
        _memory = _memory[:length]
        # 生成Memory对象，在类内描述一片内存
        memory_obj = self.Memory(memory=_memory, size=length, idx=self.memory_index, in_use=False)
        self.memory_dict[self.memory_index] = memory_obj
        self.memory_index += 1
        return memory_obj.idx

    def free_buffer(self, fd):
        return self.memory_dict.pop(fd)

    def get_buffer(self, fd, length):
        return self.memory_dict[fd].memory[:length]

    def send_open(self, chnl, prt, dma_num, length, offset=0):
        raise RuntimeError("Not supported yet")

    def recv_open(self, chnl, prt, dma_num, length, offset=0):
        pass

    def _recv(self):
        pass

    def wait_dma(self, fd, timeout: int = 0):
        pass

    def break_dma(self, fd):
        pass

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        pass
