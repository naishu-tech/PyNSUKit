import re
import socket
import struct
import threading
import ctypes
import time
from threading import Lock, Event
from dataclasses import dataclass, field
from typing import Union, Dict

import numpy as np

from .base import BaseCmdUItf, BaseChnlUItf
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
    return recv_cmd[3]


class TCPCmdUItf(BaseCmdUItf):
    _timeout = 5

    def __init__(self):
        self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.set_timeout(self._timeout)
        self.busy_lock = Lock()

    def accept(self, target: str, port: int, **kwargs):
        """

        @param target: IP地址
        @param port:
        @return:
        """
        with self.busy_lock:
            self.close()
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_timeout(self._timeout)
            self._tcp_server.connect((target, port))

    def recv_bytes(self, size: int) -> bytes:
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
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 20)
        return int.from_bytes(result, "little")

    def read(self, addr: int) -> int:
        cmd = self._fmt_reg_read(addr)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 20)
        return int.from_bytes(result, "little")

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


def get_port(ip):
    ip_match = r'^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$'
    if len(ip) >= 12 and re.match(ip_match, ip):
        _port = ip.split('.')[3][-2:]
        _port = _port[0] + '00' + _port[1]
        return _port
    else:
        return 6001


class TCPChnlUItf(BaseChnlUItf):
    _local_port = 0
    _timeout = 10

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

    def accept(self, target: str, port: int = 0, **kwargs):
        if not self.open_flag:
            self._local_port = get_port(ip=target) if port == 0 else port
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_timeout(self._timeout)
            logging.info(msg='TCP connection established')

    def set_timeout(self, value=2):
        self._tcp_server.settimeout(value)

    def open_board(self):
        self.open_flag = True
        self._tcp_server.bind(('0.0.0.0', self._local_port))
        self._tcp_server.listen(10)

    def close_board(self):
        if self.open_flag:
            try:
                self._tcp_server.close()
                self._recv_server.shutdown(socket.SHUT_RDWR)
                self._recv_server.close()
                self.open_flag = False
            except Exception as e:
                self.open_flag = False
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

    def send_open(self, chnl, prt, length, offset=0):
        raise RuntimeError("Not supported yet")

    def recv_open(self, chnl, prt, length, offset=0):
        try:
            if not self.open_flag:
                raise RuntimeError("You must use open_board first")
            if self._recv_server is not None and self._recv_thread.is_alive():
                raise RuntimeError("Too many recv_thread")
            self._recv_server, self._recv_addr = self._tcp_server.accept()
            logging.info(msg="Client connection")
            self._recv_server.settimeout(self._timeout)
            event = self.stop_event
            self._recv_thread = threading.Thread(target=self._recv, args=(prt, length, offset, event),
                                                 daemon=True, name='TCP_recv')
            self._recv_thread.start()
        except Exception as e:
            logging.error(msg=e)
            return False
        return True

    def _recv(self, prt, length, offset, event):
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
            try:
                if event.is_set():
                    memory_object.using_event.clear()
                    return memory_object.using_size

                fd = self._recv_server.recv(length * 4)
                fd_len = len(fd)
                if fd_len == 0:
                    memory_object.using_event.clear()
                    logging.info("Recv complete")
                    break

                # logging.debug(msg=f"Recv data is: {fd.hex()}")

                memory_object.memory[write_len + offset:write_len + offset + fd_len // 4] = np.frombuffer(fd,
                                                                                                          dtype='u4')
                write_len += (fd_len // 4)

                memory_object.using_size = memory_object.using_size + (write_len + offset + fd_len // 4) - (
                            write_len + offset)

                if length == 0:
                    memory_object.using_event.clear()
                    return memory_object.using_size

                length -= fd_len // 4
            except Exception as e:
                logging.error(msg=e)
                memory_object.using_event.clear()
                break

    def wait_dma(self, fd, timeout: int = 0):
        if not self.open_flag:
            raise RuntimeError("You must use open_board first")
        if not self._recv_thread.is_alive():
            raise RuntimeError("recv_thread not alive")
        if fd not in self.memory_dict:
            raise RuntimeError(f"没有此内存块")
        memory = self.memory_dict[fd]
        try:
            memory.using_event.wait(timeout)
            return memory.using_size
        except RuntimeError as e:
            logging.error(msg=e)

    def break_dma(self, fd):
        if not self.open_flag:
            raise RuntimeError("You must use open_board first")
        self.stop_event.set()
        while self._recv_thread.is_alive():
            time.sleep(0.2)
            continue
        self.stop_event.clear()
        return self.memory_dict[fd].using_size

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        if not self.recv_open(chnl=chnl, prt=fd, length=length, offset=offset):
            return False
        while True:
            try:
                if stop_event.is_set():
                    break
                if self.wait_dma(fd, time_out) == length:
                    break
                else:
                    continue
            except Exception as e:
                logging.error(msg=e)
                break

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        raise RuntimeError("Not supported yet")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close_board()
