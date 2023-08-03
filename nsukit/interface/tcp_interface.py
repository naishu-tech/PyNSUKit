import socket
import threading
import ctypes
from threading import Lock, Event
from dataclasses import dataclass, field
from typing import Union, Dict

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
    _timeout = 10
    DISCONNECT = 0

    @dataclass
    class Memory:
        memory: np.ndarray
        size: int
        idx: int
        using_event: Event = field(default_factory=Event)

        def __post_init__(self):
            self.lock: Lock = Lock()
            self._u_size: int = 0

        @property
        def using_size(self):
            with self.lock:
                return self._u_size

        @using_size.setter
        def using_size(self, value):
            with self.lock:
                self._u_size = value

    def __init__(self):
        """
        网络数据上下行接口

        """
        self.fd = None
        self.stop_event: Union[None, Event] = threading.Event()
        self._tcp_server = None
        self._recv_server = None
        self._recv_addr = None
        self.memory_dict: "Dict[int, TCPChnlUItf.Memory]" = {}
        self.memory_index = 0
        self.open_flag = False
        self._recv_thread: threading.Thread = None

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


    def set_timeout(self, value=2):
        self._tcp_server.settimeout(value)

    def open_board(self):
        if not self.open_flag:
            self._recv_server, self._recv_addr = self._tcp_server.accept()
            self._recv_server.settimeout(self._timeout)

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
        memory_obj = self.Memory(memory=_memory, size=length, idx=self.memory_index, using_event=Event())
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
        try:
            event = self.stop_event
            self._recv_thread = threading.Thread(target=self._recv, args=(chnl, prt, dma_num, length, offset, event),
                                                 daemon=True, name='TCP_recv')
            self._recv_thread.start()
        except Exception as e:
            logging.error(msg=e)
            return False
        return True

    def _recv(self, chnl, prt, dma_num, length, offset, event):
        if prt not in self.memory_dict:
            raise RuntimeError(f"没有此内存块")
        memory_object = self.memory_dict[prt]
        if memory_object.using_event.is_set():
            raise RuntimeError("内存正在被使用")
        memory_object.using_event.set()
        if length > memory_object.size:
            raise RuntimeError(f"数据大小超过内存大小")
        if length > (memory_object.size - offset):
            raise RuntimeError(f"偏移量过大")
        write_len = 0
        while True:
            if (length - write_len) * 4 > 1024:
                recv_len = 1024
            else:
                recv_len = (length - write_len) * 4
            if event.is_set():
                return memory_object.using_size
            try:
                fd = self._recv_server.recv(recv_len)
            except Exception as e:
                logging.error(msg=e)
                self.open_board()
                continue
            fd_len = len(fd)
            memory_object.memory[write_len + offset:write_len + offset + fd_len // 4] = np.frombuffer(fd, dtype='u4')
            # logging.debug(msg=f"{fd.hex()}")
            write_len += (fd_len // 4)
            memory_object.using_size = memory_object.using_size + (write_len + offset + fd_len // 4) - (
                        write_len + offset)
            if write_len == length:
                return memory_object.using_size

    def wait_dma(self, fd, timeout: int = 0):
        memory = self.memory_dict[fd]
        try:
            memory.using_event.wait(timeout)
        except TimeoutError as e:
            ...
        return memory.using_size

    def break_dma(self, fd):
        self.stop_event.set()
        while self._recv_thread.is_alive():
            continue
        self.stop_event.clear()
        return self.memory_dict[fd].using_size

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        if not self.recv_open(chnl=chnl, prt=fd, dma_num=0, length=length, offset=offset):
            return False
        while True:
            try:
                if self.wait_dma(fd, 5) == length:
                    break
                else:
                    continue
            except Exception as e:
                logging.error(msg=e)
                break

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        raise RuntimeError("Not supported yet")
