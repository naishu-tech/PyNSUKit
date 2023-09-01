# Copyright (c) [2023] [Mulan PSL v2]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import time
from threading import Lock, Event

import numpy as np

from .base import BaseCmdUItf, BaseChnlUItf, RegOperationMixin
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
    _break_status = bool
    ADDR_SENT_DOWN = 48 * (1024 ** 2) // 4 - 1
    lock = Lock()
    irq_num = 15

    def __init__(self):
        self.board = 0
        self.xdma = Xdma()
        self.timeout = self._timeout
        self.sent_base = 0
        self.recv_base = 0
        self.sent_ptr = 0
        self.recv_ptr = 0
        self.irq_base = 0
        self.sent_down_base = 0
        self.recv_event = Event()
        self.open_flag = False

    def open_board(self):
        """!
        @brief 开启板卡
        @details 使用fpga_open开启板卡
        @return
        """
        if not self.open_flag:
            self.xdma.open_board(self.board)
            self.open_flag = True

    def close_board(self):
        """!
        @brief 关闭板卡
        @details 使用fpga_close关闭板卡
        @return
        """
        if self.open_flag:
            self.xdma.close_board(self.board)
            self.open_flag = False

    def accept(self, board, sent_base, recv_base, irq_base, sent_down_base, **kwargs):
        """!
        @brief 初始化pcie指令接口
        @details 初始化pcie指令接口，获取发送基地址，返回基地址
        @param board: 板卡号
        @param sent_base: 发送基地址
        @param recv_base: 返回基地址
        @param irq_base: 中断地址
        @param sent_down_base: 写入完成标识地址
        @param kwargs: 其他参数
        @return
        """
        self.board = board
        self.sent_base = sent_base
        self.recv_base = recv_base
        self.irq_base = irq_base
        self.sent_down_base = sent_down_base
        self.open_board()

    def close(self):
        """!
        @brief 关闭连接
        @details 关闭板卡，释放锁
        @return
        """
        self.close_board()
        if self.lock.locked():
            self.lock.release()

    def set_timeout(self, s: int):
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
        if self.open_flag:
            return self.xdma.alite_write(addr, value, self.board)

    def read(self, addr: int):
        """!
        @brief pcie读寄存器
        @details 按照输入的地址，使用fpga_rd_lite查询该地址的值并返回
        @param addr 寄存器地址
        @return 该寄存的值
        """
        return self.xdma.alite_read(addr, self.board)[1]

    def send_bytes(self, data: bytes):
        """!
        @brief icd指令使用pcie发送
        @details 只有在使用icd_parser发送指令时会用
        @param data 要发送的数据
        @return 已发送的数据长度
        """
        try:
            self.sent_ptr = 0
            total_length, sent_length = len(data), 0
            st = time.time()
            while total_length != sent_length:
                assert not self._break_status(), "Interrupt command reception"
                sent_length += self._send(data[sent_length: self._block_size + sent_length])
                assert time.time() - st < self.timeout, f"send timeout, sent {sent_length}"
            self.sent_down = True
            self.timeout -= (time.time() - st)
            return sent_length
        except AssertionError as e:
            assert 0, f"[toaxi] {e}"

    def recv_bytes(self, bufsize: int):
        """!
        @brief icd指令使用pcie接收
        @details 只有在使用icd_parser接收指令时会用
        @param bufsize 要接收数据的长度
        @return 接收到的数据
        """
        try:
            self.recv_ptr = 0
            if bufsize != 0:
                if self.wait_irq:
                    self.per_recv()
                else:
                    self.per_recv_polled()
            block_size, bytes_data, bytes_data_length = self._block_size, b"", 0
            st = time.time()
            while bytes_data_length != bufsize:
                assert not self._break_status(), "Interrupt command reception"
                if not (bufsize - bytes_data_length) // self._block_size:
                    block_size = (bufsize - bytes_data_length) % self._block_size
                cur_recv_data = self._recv(block_size)
                bytes_data += cur_recv_data
                bytes_data_length += len(cur_recv_data)
                assert time.time() - st < self.timeout, f"recv timeout, rcvd {bytes_data_length}"
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
        recv_size = size + size % 4
        recv_size //= 4
        res = np.zeros((recv_size,), dtype=np.uint32)
        for idx in range(recv_size):
            res[idx] = self.xdma.alite_read(self.recv_base + self.recv_ptr, self.board)[1]
            self.recv_ptr += 4
        return res.tobytes()[:size]

    @property
    def sent_down(self):
        return self.xdma.alite_read(self.sent_base + self.ADDR_SENT_DOWN * 4, self.board)[1]

    @sent_down.setter
    def sent_down(self, value):
        """!
        @brief 标识
        @details 数据写入完成标识
        @return
        """
        if value:
            self.xdma.alite_write(self.sent_down_base, 1, self.board)
            time.sleep(0.02)
            self.xdma.alite_write(self.sent_down_base, 0, self.board)

    def reset_irq(self):
        """!
        @brief 重置中断
        @details 重置fpga给的中断
        @return
        """
        self.xdma.alite_write(self.irq_base, 0x80000000, self.board)
        time.sleep(0.2)
        self.xdma.alite_write(self.irq_base, 0x0, self.board)

    def per_recv(self, callback=None):
        """!
        @brief 接收数据前
        @details 在接收数据前运行，等待数据准备完成
        @param callback 回调函数
        @return
        """
        res = self.xdma.wait_irq(self.irq_num, self.board, self.timeout * 1000)
        if not res:
            raise TimeoutError(f'toaxi timeout')
        if callable(callback):
            callback()
        self.reset_irq()
        self.recv_event.set()

    def per_recv_polled(self):
        timeout = self.timeout
        while True:
            if self.xdma.alite_read(self.irq_base, self.board)[1] != 0x8000:
                time.sleep(1)
                if timeout > 0:
                    timeout -= 1
                else:
                    raise TimeoutError(f'toaxi timeout')
            else:
                self.reset_irq()
                self.recv_event.set()
                break

    def __enter__(self):
        self.lock.acquire(timeout=self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close()


class PCIEChnlUItf(BaseChnlUItf, RegOperationMixin):
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

    def accept(self, board, **kwargs):
        """!
        @brief 连接
        @details 连接对应板卡
        @param board 板卡逻辑id
        @param kwargs 其他参数
        @return
        """
        if not self.open_flag:
            self.board = board

    def open_board(self):
        """!
        @brief 开启板卡
        @details 使用fpga_open开启对应pcie设备
        @return
        """
        if not self.open_flag and self.board != None:
            self.xdma.open_board(self.board)
            self.open_flag = True

    def close_board(self):
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
        if self.open_flag:
            return self.xdma.alloc_buffer(self.board, length, buf)

    def free_buffer(self, fd):
        """!
        @brief 释放一片内存
        @details 使用fpga_free_dma在pcie设备上释放一片内存，该内存为输入的内存
        @param fd 要释放的内存地址
        @return True/Flse
        """
        return self.xdma.free_buffer(fd)

    def get_buffer(self, fd, length):
        """!
        @brief 获取内存中的值
        @details 使用fpga_get_dma_buffer在pcie设备上获取一片内存的数据
        @param fd 内存地址
        @param length 获取长度
        @return 内存中存储的数据
        """
        return self.xdma.get_buffer(fd, length)

    def send_open(self, chnl, fd, length, offset=0):
        """!
        @brief 数据下行开启
        @details 开启数据流下行
        @param chnl 通道号
        @param fd 一片内存的地址
        @param length 数据长度
        @param offset 内存偏移量
        @return
        """
        if self.open_flag:
            return self.xdma.fpga_send(self.board, chnl, fd, length, offset=offset)

    def recv_open(self, chnl, fd, length, offset=0):
        """!
        @brief 数据上行开启
        @details 开启数据流上行
        @param chnl 通道号
        @param fd 一片内存的地址
        @param length 数据长度
        @param offset 内存偏移量
        @return
        """
        if self.open_flag:
            return self.xdma.fpga_recv(self.board, chnl, fd, length, offset=offset)

    def wait_dma(self, fd, timeout: int = 0):
        """!
        @brief 等待完成一次dma操作
        @details 等待所有数据写入内存
        @param fd 内存地址
        @param timeout 超时时间
        @return 已经写入内存中数据的大小
        """
        return self.xdma.wait_dma(fd, timeout)

    def break_dma(self, fd):
        """!
        @brief 终止本次dma操作
        @details 停止向内存中写入数据
        @param fd 内存地址
        @return 已经写入内存中数据的大小
        """
        return self.xdma.break_dma(fd=fd)

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
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
        @return True/False
        """
        if self.open_flag:
            return self.xdma.stream_read(self.board, chnl, fd, length, offset, stop_event, time_out, flag)

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
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
        @return True/False
        """
        if self.open_flag:
            return self.xdma.stream_write(self.board, chnl, fd, length, offset, stop_event, time_out, flag)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close_board()
