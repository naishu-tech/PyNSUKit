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
import time
from threading import Lock, Event
from typing import Callable

import numpy as np

from .base import BaseCmdUItf, BaseStreamUItf, RegOperationMixin, InitParamSet
from ..tools.xdma import Xdma


class PCIECmdUItf(BaseCmdUItf):
    """!
    @brief PCIE指令接口
    @details 包括连接/断开、发送、接收等功能
    @image html professional_PCI-E_cmd.png
    """
    wait_irq = False
    _once_send_or_recv_timeout = 1  # _break_status状态改变间隔应超过该值
    _timeout = 30
    _block_size = 4096
    ADDR_SENT_DOWN = 48 * (1024 ** 2) // 4 - 1
    irq_num = 15
    multi_board_lock = Lock()

    def __init__(self):
        self.board = 0
        self.xdma: Xdma = Xdma()
        self.timeout = self._timeout
        self.once_timeout = self.timeout
        self.sent_base = 0
        self.recv_base = 0
        self.sent_ptr = 0
        self.recv_ptr = 0
        self.irq_base = 0
        self.sent_down_base = 0
        self.recv_event = Event()
        self.open_flag = True

    def accept(self, param: InitParamSet) -> None:
        """!
        @brief 初始化pcie指令接口
        @details 初始化pcie指令接口，获取发送基地址，返回基地址
        @param param:
            - InitParamSet或其子类的对象，需包含cmd_board、cmd_sent_base、cmd_recv_base、cmd_irq_base、cmd_sent_down_base属性
            - board: 板卡号
            - sent_base: 发送基地址
            - recv_base: 返回基地址
            - irq_base: 中断地址
            - sent_down_base: 写入完成标识地址
        @return None
        """
        self.board = param.cmd_board
        self.sent_base = param.cmd_sent_base
        self.recv_base = param.cmd_recv_base
        self.irq_base = param.cmd_irq_base
        self.sent_down_base = param.cmd_sent_down_base
        self.xdma.open_board(self.board)
        self.open_flag = True

    def close(self) -> None:
        """!
        @brief 关闭连接
        @details 关闭板卡，释放锁
        @return None
        """
        if self.open_flag:
            self.xdma.close_board(self.board)
            self.open_flag = False

    def set_timeout(self, s: float) -> None:
        """!
        @brief 设置超时时间
        @details 设置pcie指令的超时时间
        @param s 秒
        @return
        """
        self.timeout = s

    def write(self, addr: int, value: int):
        """!
        @brief pcie写寄存器
        @details 按照输入的地址、值，使用fpga_wr_lite写入目标寄存器
        @param addr 寄存器地址
        @param value 要写入的值
        @return True/False
        """
        if not self.open_flag:
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Not connected to the board {self.board}.')
        value = struct.unpack('=I', value)[0]
        if not self.xdma.alite_write(addr, value, self.board):
            self.open_flag = False
            raise RuntimeError(f'{self.__class__.__name__}.{self.write.__name__}: '
                               f'Failed to write to register {hex(addr)} on board {self.board}')

    def read(self, addr: int) -> bytes:
        """!
        @brief pcie读寄存器
        @details 按照输入的地址，使用fpga_rd_lite查询该地址的值并返回
        @param addr 寄存器地址
        @return 该寄存的值
        """
        if not self.open_flag:
            raise RuntimeError(f'{self.__class__.__name__}.{self.read.__name__}: '
                               f'Not connected to the board {self.board}.')
        res = self.xdma.alite_read(addr, self.board)
        if not res[0]:
            raise RuntimeError(f'{self.__class__.__name__}.{self.read.__name__}: '
                               f'Failed to read from register {hex(addr)} on board {self.board}')
        return struct.pack('=I', res[1])

    def send_down(self):
        self.sent_ptr = 0
        self._sent_down = True

    def recv_down(self):
        self.recv_ptr = 0
        self.reset_irq()
        self.recv_event.set()

    def send_bytes(self, data: bytes) -> int:
        """!
        @brief      icd指令使用pcie发送
        @details    只有在使用icd_parser发送指令时会用
        @param data 要发送的数据
        @return     已发送的数据长度
        """
        if not self.open_flag:
            raise RuntimeError(f'{self.__class__.__name__}.{self.send_bytes.__name__}: '
                               f'Not connected to the board {self.board}.')
        try:
            self.once_timeout = self.timeout
            total_length, sent_length = len(data), 0
            st = time.time()
            while total_length != sent_length:
                sent_length += self._send(data[sent_length: self._block_size + sent_length])
                assert time.time() - st < self.once_timeout, f"send timeout, sent {sent_length}"
            self.once_timeout -= (time.time() - st)
            return sent_length
        except AssertionError as e:
            assert 0, f"[toaxi] {e}"

    def recv_bytes(self, size: int) -> bytes:
        """!
        @brief icd指令使用pcie接收
        @details 只有在使用icd_parser接收指令时会用
        @param size 要接收数据的长度
        @return 接收到的数据
        """
        if not self.open_flag:
            raise RuntimeError(f'{self.__class__.__name__}.{self.recv_bytes.__name__}: '
                               f'Not connected to the board {self.board}.')
        try:
            if size != 0:
                if self.wait_irq:
                    self.per_recv()
                else:
                    self.per_recv_polled()
            block_size, bytes_data, bytes_data_length = self._block_size, b"", 0
            st = time.time()
            while bytes_data_length != size:
                if not (size - bytes_data_length) // self._block_size:
                    block_size = (size - bytes_data_length) % self._block_size
                cur_recv_data = self._recv(block_size)
                bytes_data += cur_recv_data
                bytes_data_length += len(cur_recv_data)
                assert time.time() - st < self.once_timeout, f"recv timeout, rcvd {bytes_data_length}"
        except (AssertionError, TimeoutError) as e:
            assert 0, f"[toaxi] {e}"
        return bytes_data

    def _send(self, data):
        """!
        @brief 指令发送
        @details 数据不满足4Bytes整倍数的，被自动补齐为4Bytes整倍数，使用wr_lite写入数据
        @param data 要发送的数据
        @return 已经发送的数据长度
        """
        with self.multi_board_lock:
            data += b'\x00' * (len(data) % 4)
            data = np.frombuffer(data, dtype=np.uint32)
            for value in data:
                self.xdma.alite_write(self.sent_base + self.sent_ptr, value, self.board)
                self.sent_ptr += 4
            return int(data.nbytes)

    def _recv(self, size):
        """!
        @brief 指令接收
        @details 使用rd_lite读取数据
        @param size 要接收的数据大小
        @return 接收的数据
        """
        with self.multi_board_lock:
            recv_size = size + size % 4
            recv_size //= 4
            res = np.zeros((recv_size,), dtype=np.uint32)
            for idx in range(recv_size):
                res[idx] = self.xdma.alite_read(self.recv_base + self.recv_ptr, self.board)[1]
                self.recv_ptr += 4
            return res.tobytes()[:size]

    @property
    def _sent_down(self):
        return self.xdma.alite_read(self.sent_base + self.ADDR_SENT_DOWN * 4, self.board)[1]

    @_sent_down.setter
    def _sent_down(self, value):
        """!
        @brief 标识
        @details 数据写入完成标识
        @return
        """
        if value:
            self.xdma.alite_write(self.sent_down_base, 1, self.board)
            time.sleep(0.001)
            self.xdma.alite_write(self.sent_down_base, 0, self.board)

    def reset_irq(self):
        """!
        @brief 重置中断
        @details 重置fpga给的中断
        @return
        """
        self.xdma.alite_write(self.irq_base, 0x80000000, self.board)
        time.sleep(0.001)
        self.xdma.alite_write(self.irq_base, 0x0, self.board)

    def per_recv(self, callback=None):
        """!
        @brief 接收数据前
        @details 在接收数据前运行，等待数据准备完成
        @param callback 回调函数
        @return
        """
        res = self.xdma.wait_irq(self.irq_num, self.board, self.once_timeout * 1000)
        if not res:
            raise TimeoutError(f'toaxi timeout')
        if callable(callback):
            callback()

    def per_recv_polled(self):
        timeout = self.once_timeout
        while self.xdma.alite_read(self.irq_base, self.board)[1] != 0x8000:
            time.sleep(0.001)
            if timeout > 0:
                timeout -= 0.005
            else:
                raise TimeoutError(f'toaxi timeout')


class PCIEStreamUItf(BaseStreamUItf, RegOperationMixin):
    """!
    @brief PCIE数据流接口
    @details 包括连接/断开、内存操作、接收/等待/终止等功能
    @image html professional_PCI-E_data.png
    """

    def __init__(self):
        self.xdma = Xdma()
        self.board = None
        self.open_flag = False

    def reg_write(self, addr, value) -> bool:
        if self.open_flag:
            return self.xdma.alite_write(addr, value, self.board)

    def reg_read(self, addr) -> int:
        if self.open_flag:
            return self.xdma.alite_read(addr, self.board)[1]

    def accept(self, param: InitParamSet) -> None:
        """!
        @brief 连接
        @details 连接对应板卡
        @param param InitParamSet或其子类的对象，需包含stream_board属性
        @return
        """
        self.board = param.stream_board
        if not self.open_flag:
            self.open_flag = self.xdma.open_board(self.board)

    def close(self) -> None:
        """!
        @brief 关闭板卡
        @details 使用fpga_close关闭对应pcie设备
        @return
        """
        if self.open_flag:
            self.xdma.close_board(self.board)
            self.open_flag = False

    def alloc_buffer(self, length, buf: int = None):
        """!
        @brief 申请一片内存
        @details 使用fpga_alloc_dma在pcie设备上申请一片内存，该内存与pcie设备绑定
        @param length 申请长度
        @param buf 内存类型
        @return 申请的内存的地址
        """
        if length % 4 != 0:
            raise ValueError(f'in {self.__class__.__name__}, stream mem length should be multiple of 4')
        if self.open_flag:
            return self.xdma.alloc_buffer(self.board, length//4, buf)

    def free_buffer(self, fd: int):
        """!
        @brief 释放一片内存
        @details 使用fpga_free_dma在pcie设备上释放一片内存，该内存为输入的内存
        @param fd 要释放的内存地址
        @return True/Flse
        """
        return self.xdma.free_buffer(fd)

    def get_buffer(self, fd: int, length: int) -> np.ndarray:
        """!
        @brief 获取内存中的值
        @details 使用fpga_get_dma_buffer在pcie设备上获取一片内存的数据
        @param fd 内存地址
        @param length 获取长度
        @return 内存中存储的数据
        """
        if length % 4 != 0:
            raise ValueError(f'in {self.__class__.__name__}, stream mem length should be multiple of 4')
        return self.xdma.get_buffer(fd, length//4)

    def open_send(self, chnl: int, fd: int, length: int, offset: int = 0) -> None:
        """!
        @brief 数据下行开启
        @details 开启数据流下行
        @param chnl 通道号
        @param fd 一片内存的地址
        @param length 数据长度
        @param offset 内存偏移量
        @return
        """
        if length % 4 != 0:
            raise ValueError(f'in {self.__class__.__name__}, stream mem length should be multiple of 4')
        if self.open_flag:
            return self.xdma.fpga_send(self.board, chnl, fd, length//4, offset=offset//4)

    def open_recv(self, chnl: int, fd: int, length: int, offset: int = 0) -> None:
        """!
        @brief 数据上行开启
        @details 开启数据流上行
        @param chnl 通道号
        @param fd 一片内存的地址
        @param length 数据长度
        @param offset 内存偏移量
        @return
        """
        if length % 4 != 0:
            raise ValueError(f'in {self.__class__.__name__}, stream mem length should be multiple of 4')
        if self.open_flag:
            return self.xdma.fpga_recv(self.board, chnl, fd, length//4, offset=offset//4)

    def wait_stream(self, fd: int, timeout: float = 0.) -> int:
        """!
        @brief 等待完成一次dma操作
        @details 等待所有数据写入内存
        @param fd 内存地址
        @param timeout 超时时间
        @return 已经写入内存中数据的大小
        """
        timeout = int(timeout)
        return self.xdma.wait_dma(fd, int(timeout*1000))

    def break_stream(self, fd):
        """!
        @brief 终止本次dma操作
        @details 停止向内存中写入数据
        @param fd 内存地址
        @return 已经写入内存中数据的大小
        """
        self.xdma.break_dma(fd=fd)

    def stream_recv(self, chnl: int, fd: int, length: int, offset: int = 0,
                    stop_event: Callable = None, time_out: float = 1., flag: int = 1) -> None:
        """!
        @brief 数据流上行
        @details 封装好的数据流上行函数
        @param chnl 通道号
        @param fd 内存地址
        @param length 数据长度
        @param offset 内存偏移量
        @param stop_event 外部停止信号
        @param time_out 超时时间
        @param flag 1
        @return
        """
        time_out = int(time_out*1000)
        if length % 4 != 0:
            raise ValueError(f'in {self.__class__.__name__}, stream mem length should be multiple of 4')
        if self.open_flag:
            return self.xdma.stream_read(self.board, chnl, fd, length//4, offset//4, stop_event, time_out, flag)

    def stream_send(self, chnl: int, fd: int, length: int, offset: int = 0,
                    stop_event: Callable = None, time_out: float = 1., flag: int = 1) -> None:
        """!
        @brief 数据流下行
        @details 封装好的数据流下行函数
        @param chnl 通道号
        @param fd 内存地址
        @param length 数据长度
        @param offset 内存偏移量
        @param stop_event 外部停止信号
        @param time_out 超时时间
        @param flag 1
        @return
        """
        time_out = int(time_out*1000)
        if length % 4 != 0:
            raise ValueError(f'in {self.__class__.__name__}, stream mem length should be multiple of 4')
        if self.open_flag:
            return self.xdma.stream_write(self.board, chnl, fd, length//4, offset//4, stop_event, time_out, flag)
