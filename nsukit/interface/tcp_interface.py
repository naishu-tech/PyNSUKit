# Copyright (c) [2023] [NaiShu]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import re
import socket
import struct
import threading
import ctypes
import time
from threading import Lock, Event
from dataclasses import dataclass, field
from typing import Union, Dict, Iterable, Callable

import numpy as np

from .base import BaseCmdUItf, VirtualRegCmdMixin, BaseStreamUItf, InitParamSet
from ..tools.logging import logging


class TCPCmdUItf(VirtualRegCmdMixin, BaseCmdUItf):
    """!
    @brief 网络指令接口
    @details 包括连接/断开、发送、接收等功能
    @image html professional_tcp_cmd.png
    """
    _timeout = 15

    def __init__(self):
        self.addr = 'xxx.xxx.xxx.xxx'
        self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.set_timeout(self._timeout)
        self.busy_lock = Lock()

    def accept(self, param: InitParamSet):
        """!
        @brief 初始化网络指令接口
        @details 初始化网络指令接口，获取IP地址，端口号等参数
        @param param InitParamSet或其子类的对象，需包含cmd_ip、cmd_tcp_port属性
        @return
        """
        with self.busy_lock:
            self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.set_timeout(self._timeout)
            self._tcp_server.connect((param.cmd_ip, param.cmd_tcp_port))
            self.addr = param.cmd_ip

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
        @brief      发送数据
        @details    使用网络发送数据
        @param data 要发送的数据
        @return     发送完成的数据长度
        """
        with self.busy_lock:
            total_len = len(data)
            total_sendlen = 0
            while True:
                send_len = self._tcp_server.send(data[total_sendlen:])
                total_sendlen += send_len
                if total_len == total_sendlen:
                    return total_len
                if send_len == 0:
                    raise RuntimeError("Connection interruption")

    def write(self, addr: int, value: bytes) -> None:
        """!
        @brief 发送数据
        @details 使用网络以地址值的方式发送一条约定好的特殊指令
        @param addr 要修改的地址
        @param value 地址中要赋的值
        @return 无
        """
        return self._common_write(addr, value, self.addr)

    def read(self, addr: int) -> bytes:
        """!
        @brief 接收数据
        @details 使用网络以地址的方式发送一条约定好的特殊指令
        @param addr 要读取的地址
        @return 返回读取到的结果
        """
        return self._common_read(addr, self.addr)

    def close(self) -> None:
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

    def set_timeout(self, s: float = 1.) -> None:
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
    ip_match = (r'^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|'
                r'2[0-4]\d|25[0-5]|[1-9]\d|\d)\.(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)$')
    if len(ip) >= 12 and re.match(ip_match, ip):
        _port = ip.split('.')[3][-2:]
        _port = _port[0] + '00' + _port[1]
        return int(_port)
    else:
        return 6001


class TCPStreamUItf(BaseStreamUItf):
    """!
    @brief 网络数据流接口
    @details 包括连接/断开、内存操作、接收/等待/终止等功能
    @image html professional_tcp_data.png
    """
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
        self._local_port = 0
        self.memory_dict: "Dict[int, TCPStreamUItf.Memory]" = {}
        self.memory_index = 0
        self.open_flag = False
        self._recv_thread: threading.Thread = threading.Thread()
        self._recv_stop= threading.Event()

    def accept(self, param: InitParamSet) -> None:
        """!
        @brief 连接
        @details 根据IP地址端口号建立连接
        @param param InitParamSet或其子类的对象，需包含stream_ip、stream_tcp_port属性
        @return
        """
        if self.open_flag:
            self.close()
        self._local_port = get_port(ip=param.stream_ip) if param.stream_tcp_port == 0 else param.stream_tcp_port
        self._tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.set_timeout(self._timeout)
        self._tcp_server.bind(('0.0.0.0', self._local_port))
        self._tcp_server.listen(10)
        logging.info(msg='TCP connection established')
        self.open_flag = True
        self._recv_server = None

    def set_timeout(self, s: float = 2) -> None:
        """!
        @brief 设置超时时间
        @details 根据传入的数值设置TCPServer的超时时间
        @param s 秒
        @return
        """
        self._tcp_server.settimeout(s)

    def close(self) -> None:
        """!
        @brief 关闭连接
        @details 关闭server以及用于传输数据的子链接
        @return
        """
        if self.open_flag:
            try:
                self._tcp_server.close()
                if self._recv_server is not None:
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

    def free_buffer(self, fd: int):
        """!
        @brief 释放一片内存
        @details 使用fpga_free_dma在pcie设备上释放一片内存，该内存为输入的内存
        @param fd 要释放的内存地址
        @return True/False
        """
        try:
            self.memory_dict.pop(fd)
            return True
        except Exception:
            return False

    def get_buffer(self, fd: int, length: int) -> np.ndarray:
        """!
        @brief 获取内存中的值
        @details 根据内存的key获取内存中存储的数据
        @param fd 内存地址
        @param length 获取长度
        @return 内存中存储的数据
        """
        return self.memory_dict[fd].memory[:length]

    def open_send(self, chnl: int, fd: int, length: int, offset: int = 0) -> None:
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

    def open_recv(self, chnl: int, fd: int, length: int, offset: int = 0) -> None:
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
            if self._recv_thread.is_alive():
                raise RuntimeError("Too many recv_thread")
            if self._recv_server is None:
                self._recv_server, self._recv_addr = self._tcp_server.accept()
                logging.info(msg=f"{self.__class__.__name__} Client connection")
            event = self.stop_event
            self._recv_thread = threading.Thread(target=self._recv, args=(fd, length, offset, event),
                                                 daemon=True, name='TCP_recv')
            self._recv_thread.start()
        except Exception as e:
            logging.error(msg=e)
            raise e

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
        self._recv_stop.clear()
        if length > memory_object.size:
            raise RuntimeError(f"数据大小超过内存大小")
        if length > (memory_object.size - offset):
            raise RuntimeError(f"偏移量过大")
        if length % 4 != 0:
            raise RuntimeError(f"数据不能被4整除")
        recv_length = length * 4
        data = b''
        data_len = 0
        while True:
            try:
                if event.is_set():
                    memory_object.using_event.clear()
                    return memory_object.using_size
                _data = self._recv_server.recv(recv_length - data_len)
                data += _data
                data_len = len(data)
                if data_len >= recv_length:
                    memory_object.memory[offset:offset + data_len // 4] = np.frombuffer(data, dtype='u4')
                    memory_object.using_size = data_len // 4
                    memory_object.using_event.clear()
                    break
            except Exception as e:
                logging.error(msg=e)
                memory_object.using_event.clear()
                break
        self._recv_stop.set()

    def wait_stream(self, fd: int, timeout: float = 0.) -> int:
        """!
        @brief 等待完成一次dma操作
        @details 等待所有数据写入内存
        @param fd 内存标号(key)
        @param timeout 超时时间
        @return 已经写入内存中数据的大小
        """
        if not self.open_flag:
            raise RuntimeError("You must use open_board first")
        if fd not in self.memory_dict:
            raise RuntimeError(f"没有此内存块")
        memory = self.memory_dict[fd]
        try:
            memory.using_event.wait(timeout)
            return memory.using_size
        except RuntimeError as e:
            logging.error(msg=e)

    def break_stream(self, fd: int) -> None:
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

    def stream_recv(self, chnl: int, fd: int, length: int, offset: int = 0,
                    stop_event: Callable = None, time_out: float = 1., flag: int = 1) -> None:
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
        self.open_recv(chnl=chnl, fd=fd, length=length, offset=offset)
        while True:
            try:
                if stop_event():
                    break
                if self.wait_stream(fd, time_out) == length:
                    self._recv_stop.wait(timeout=5)
                    break
            except Exception as e:
                logging.error(msg=e)
                break

    def stream_send(self, chnl: int, fd: int, length: int, offset: int = 0,
                    stop_event: Callable = None, time_out: float = 1., flag: int = 1) -> None:
        """!
        @brief 数据流下行
        @details 封装好的数据流下行函数
        @todo TCP下行数据流暂不支持
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
