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


class TCPCmdUItf(BaseCmdUItf):
    """!
    @brief 网络指令接口
    @details 包括连接/断开、发送、接收等功能
    """
    _timeout = 15

    def __init__(self):
        self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.set_timeout(self._timeout)
        self.busy_lock = Lock()

    def accept(self, target: str, port: int, **kwargs):
        """!
        @brief 初始化网络指令接口
        @details 初始化网络指令接口，获取IP地址，端口号等参数
        @param target IP地址
        @param port 端口号
        @param kwargs 其他参数
        @return
        """
        with self.busy_lock:
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_timeout(self._timeout)
            self._tcp_server.connect((target, port))

    def recv_bytes(self, size: int) -> bytes:
        """!
        @brief 接收数据
        @details 使用网络接收指定大小的数据
        @param size 接收数据的长度
        @return 接收到的数据
        """
        with self.busy_lock:
            recv_data = b''
            recv_size = 0
            while True:
                if recv_size != size:
                    data = self._tcp_server.recv(size-recv_size)
                    recv_data += data
                    recv_size += len(data)
                if recv_size >= size:
                    break
            return recv_data

    def send_bytes(self, data: bytes) -> int:
        """!
        @brief 发送数据
        @details 使用网络发送数据
        @param data 要发送的数据
        @return 发送完成的数据长度
        """
        with self.busy_lock:
            total_len = len(data)
            total_sendlen = 0
            while True:
                send_len = self._tcp_server.send(data)
                total_sendlen += send_len
                if total_len == total_sendlen:
                    return total_len
                if send_len == 0:
                    raise RuntimeError("Connection interruption")

    def write(self, addr: int, value: bytes) -> bytes:
        """!
        @brief 发送数据
        @details 使用网络以地址值的方式发送一条约定好的特殊指令
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
        return result

    def read(self, addr: int) -> bytes:
        """!
        @brief 接收数据
        @details 使用网络以地址的方式发送一条约定好的特殊指令
        @param addr 要读取的地址
        @return 返回读取到的结果
        """
        cmd = self._fmt_reg_read(addr)
        if len(cmd) != self.send_bytes(cmd):
            raise RuntimeError(f"Fail in send")
        recv = self.recv_bytes(16)
        result_len = head_check(cmd, recv)
        result = self.recv_bytes(result_len - 16)
        return result

    def close(self):
        """!
        @brief 关闭连接
        @details 关闭网络连接
        @return
        """
        try:
            self._tcp_server.shutdown(socket.SHUT_RDWR)
            self._tcp_server.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, s: int = 5):
        """!
        @brief 设置超时时间
        @details 根据传入的数值设置串口的超时时间
        @param s 秒
        @return
        """
        self._tcp_server.settimeout(s)


def get_port(ip):
    """!
    @brief 获取数据流端口
    @details 根据目标IP地址计算出端口号
    @param ip 目标ip
    @return 计算的端口号
    """
    ip_match = r'^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$'
    if len(ip) >= 12 and re.match(ip_match, ip):
        _port = ip.split('.')[3][-2:]
        _port = _port[0] + '00' + _port[1]
        return int(_port)
    else:
        return 6001


class TCPChnlUItf(BaseChnlUItf):
    """!
    @brief 网络数据流接口
    @details 包括连接/断开、内存操作、接收/等待/终止等功能
    """
    _local_port = 0
    _timeout = 15

    @dataclass
    class Memory:
        """!
        @brief 内存类
        @details 开辟一块内存使用的类
        """
        memory: np.ndarray
        size: int
        idx: int
        using_event: Event = field(default_factory=Event)

        def __post_init__(self):
            """!
            @brief 初始化
            @details 初始化内存对象，给属性赋值
            @return
            """
            self.lock: Lock = Lock()
            self._u_size: int = 0

        @property
        def using_size(self):
            with self.lock:
                return self._u_size

        @using_size.setter
        def using_size(self, value):
            """!
            @brief 设置已经使用的内存大小
            @details 在写入数据时填入写入数据的大小
            @param value 使用的内存大小
            @return
            """
            with self.lock:
                self._u_size = value

    def __init__(self):
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
        """!
        @brief 连接
        @details 根据IP地址端口号建立连接
        @param target IP地址
        @param port 端口号
        @param kwargs 其他参数
        @return
        """
        if not self.open_flag:
            self._local_port = get_port(ip=target) if port == 0 else port
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_timeout(self._timeout)
            logging.info(msg='TCP connection established')

    def set_timeout(self, value=2):
        """!
        @brief 设置超时时间
        @details 根据传入的数值设置TCPServer的超时时间
        @param value 秒
        @return
        """
        self._tcp_server.settimeout(value)

    def open_board(self):
        """!
        @brief 监听TCP
        @details 根据设置的端口号进行监听
        @return
        """
        self.open_flag = True
        self._tcp_server.bind(('0.0.0.0', self._local_port))
        self._tcp_server.listen(10)

    def close_board(self):
        """!
        @brief 关闭连接
        @details 关闭server以及用于传输数据的子链接
        @return
        """
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
        @brief 申请一片内存
        @details 根据传入参数实例化内存类，存入字典中
        @param length 申请长度
        @param buf 内存类型
        @return 申请的内存在字典中的key
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
        """!
        @brief 释放一片内存
        @details 使用fpga_free_dma在pcie设备上释放一片内存，该内存为输入的内存
        @param fd 要释放的内存地址
        @return True/Flse
        """
        try:
            self.memory_dict.pop(fd)
            return True
        except Exception:
            return False

    def get_buffer(self, fd, length):
        """!
        @brief 获取内存中的值
        @details 根据内存的key获取内存中存储的数据
        @param fd 内存地址
        @param length 获取长度
        @return 内存中存储的数据
        """
        return self.memory_dict[fd].memory[:length]

    def send_open(self, chnl, fd, length, offset=0):
        """!
        @brief 数据下行开启
        @details 开启数据流下行
        @param chnl 未使用
        @param fd 内存标号(key)
        @param length 要发送数据的长度
        @param offset 内存偏移量
        @return
        """
        raise RuntimeError("Not supported yet")

    def recv_open(self, chnl, fd, length, offset=0):
        """!
        @brief 数据上行开启
        @details 开启数据流上行
        @param chnl
        @param fd 内存标号(key)
        @param length 要接收数据的长度
        @param offset 内存偏移量
        @return True/False
        """
        try:
            if not self.open_flag:
                raise RuntimeError("You must use open_board first")
            if self._recv_server is not None and self._recv_thread.is_alive():
                raise RuntimeError("Too many recv_thread")
            self._recv_server, self._recv_addr = self._tcp_server.accept()
            logging.info(msg="Client connection")
            self._recv_server.settimeout(self._timeout)
            event = self.stop_event
            self._recv_thread = threading.Thread(target=self._recv, args=(fd, length, offset, event),
                                                 daemon=True, name='TCP_recv')
            self._recv_thread.start()
        except Exception as e:
            logging.error(msg=e)
            return False
        return True

    def _recv(self, fd, length, offset, event):
        """!
        @brief 数据上行
        @details 数据流上行的具体实现
        @param fd 内存标号(key)
        @param length 要接收数据的长度
        @param offset 内存偏移量
        @param event 外部停止信号量
        @return 已使用内存大小
        """
        if fd not in self.memory_dict:
            raise RuntimeError(f"没有此内存块")
        memory_object = self.memory_dict[fd]
        if memory_object.using_event.is_set():
            raise RuntimeError("内存正在被使用")
        memory_object.using_event.set()
        if length > memory_object.size:
            raise RuntimeError(f"数据大小超过内存大小")
        if length > (memory_object.size - offset):
            raise RuntimeError(f"偏移量过大")
        if length % 4 != 0:
            raise RuntimeError(f"数据不能被4整除")
        write_len = 0
        while True:
            try:
                if event.is_set():
                    memory_object.using_event.clear()
                    return memory_object.using_size
                if length*4 > 1024:
                    recv_length = 1024
                else:
                    recv_length = length*4

                fd = self._recv_server.recv(recv_length)
                fd_len = len(fd)
                if fd_len < recv_length:
                    fd += self._recv_server.recv(recv_length-fd_len)
                    fd_len = len(fd)
                if fd_len == 0:
                    memory_object.using_event.clear()
                    logging.info("Recv complete")
                    break

                # logging.debug(msg=f"Recv data is: {fd.hex()}")

                memory_object.memory[write_len + offset:write_len + offset + fd_len // 4] = np.frombuffer(fd, dtype='u4')
                write_len += (fd_len // 4)

                memory_object.using_size = memory_object.using_size + (write_len + offset + fd_len // 4) - (
                            write_len + offset)

                if length <= 0:
                    memory_object.using_event.clear()
                    return memory_object.using_size

                length -= (fd_len // 4)
            except Exception as e:
                logging.error(msg=e)
                memory_object.using_event.clear()
                break

    def wait_dma(self, fd, timeout: int = 0):
        """!
        @brief 等待完成一次dma操作
        @details 等待所有数据写入内存
        @param fd 内存标号(key)
        @param timeout 超时时间
        @return 已经写入内存中数据的大小
        """
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
        """!
        @brief 终止本次dma操作
        @details 停止向内存中写入数据
        @param fd 内存标号(key)
        @return 已经写入内存中数据的大小
        """
        if not self.open_flag:
            raise RuntimeError("You must use open_board first")
        self.stop_event.set()
        while self._recv_thread.is_alive():
            time.sleep(0.2)
            continue
        self.stop_event.clear()
        return self.memory_dict[fd].using_size

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        """!
        @brief 数据流上行
        @details 封装好的数据流上行函数
        @param chnl 未使用
        @param fd 内存标号(key)
        @param length 数据长度
        @param offset 内存偏移量
        @param stop_event 外部停止信号
        @param time_out 超时时间
        @param flag 1
        @return True/False
        """
        if not self.recv_open(chnl=chnl, fd=fd, length=length, offset=offset):
            return False
        while True:
            try:
                time.sleep(0.2)
                if stop_event():
                    break
                if self.wait_dma(fd, time_out) == length:
                    return True
                else:
                    continue
            except Exception as e:
                logging.error(msg=e)
                break

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        """!
        @brief 数据流下行
        @details 封装好的数据流下行函数
        @param chnl
        @param fd 内存标号(key)
        @param length 数据长度
        @param offset 内存偏移量
        @param stop_event 外部停止信号
        @param time_out 超时时间
        @param flag 1
        @return True/False
        """
        raise RuntimeError("Not supported yet")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close_board()
