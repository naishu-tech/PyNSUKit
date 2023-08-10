import time
from threading import Lock, Event

import numpy as np

from .base import BaseCmdUItf, BaseChnlUItf
from ..tools.xdma import Xdma


class PCIECmdUItf(BaseCmdUItf):
    """!
    @brief PCIE指令接口
    @details 包括连接/断开、发送等功能
    """

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
        self.recv_event = Event()
        self.open_flag = False

    def open_board(self):
        """!
        @brief 开启板卡
        @details 使用xdma开启板卡
        @return:
        """
        if not self.open_flag:
            self.xdma.open_board(self.board)
            self.open_flag = True

    def close_board(self):
        """!
        @brief 关闭板卡
        @details 使用xdma关闭板卡
        @return:
        """
        if self.open_flag:
            self.xdma.close_board(self.board)
            self.open_flag = False

    def accept(self, board, sent_base, recv_base, **kwargs):
        """!
        @brief 初始化pcie指令接口
        @details 初始化pcie指令接口，获取发送基地址，返回基地址
        @param board: 板卡号
        @param sent_base: 发送基地址
        @param recv_base: 返回基地址
        @param kwargs:
        @return:
        """
        self.board = board
        self.sent_base = sent_base
        self.recv_base = recv_base
        self.open_board()

    def close(self):
        """!
        @brief 关闭连接
        @details 关闭板卡，释放锁
        @return:
        """
        self.close_board()
        self.lock.release()

    def set_timeout(self, s: int):
        """!
        @brief 设置超时时间
        @details 设置pcie指令的超时时间
        @param s: 秒
        :return:
        """
        self.timeout = s

    def write(self, addr: int, value: int):
        """!
        @brief pcie写寄存器
        @details 按照输入地址值方式，使用wr_lite写入目标寄存器
        @param addr: 寄存器地址
        @param value: 要写入的值
        @return: True/False
        """
        if self.open_flag:
            return self.xdma.alite_write(addr, value, self.board)

    def read(self, addr: int):
        """!

        @param addr:
        @return:
        """
        return self.xdma.alite_read(addr, self.board)[1]

    def send_bytes(self, data: bytes):
        """!

        @param data:
        @return:
        """
        try:
            total_length, sent_length = len(data), 0
            st = time.time()
            while total_length != sent_length:
                assert not self._break_status(), "Interrupt command reception"
                sent_length += self._send(data[sent_length: self._block_size + sent_length])
                assert time.time() - st < self.timeout, f"send timeout, sent {sent_length}"
            self.sent_down = True
            self.timeout -= (time.time() - st)
        except AssertionError as e:
            assert 0, f"[toaxi] {e}"

    def recv_bytes(self, bufsize: int):
        """!
        接收数据
        @param bufsize:
        @return:
        """
        try:
            if bufsize != 0:
                self.per_recv()
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
        不满足4Bytes整倍数的，被自动补齐为4Bytes整倍数
        @param data:
        @return:
        """
        data += b'\x00' * (len(data) % 4)
        data = np.frombuffer(data, dtype=np.uint32)
        for value in data:
            self.xdma.alite_write(self.sent_base + self.sent_ptr, value, self.board)
            self.sent_ptr += 4
        return int(data.nbytes)

    def _recv(self, size):
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
        if value:
            self.xdma.alite_write(0x00003030, 1, self.board)
            time.sleep(0.02)
            self.xdma.alite_write(0x00003030, 0, self.board)

    def reset_irq(self):
        self.xdma.alite_write(0 + 44, 0x80000000, self.board)
        self.xdma.alite_write(0 + 44, 0x0, self.board)

    def per_recv(self, callback=None):
        res = self.xdma.wait_irq(self.irq_num, self.board, self.timeout * 1000)
        if not res:
            raise TimeoutError(f'toaxi timeout')
        if callable(callback):
            callback()
        self.reset_irq()
        self.recv_event.set()

    def __enter__(self):
        self.lock.acquire(timeout=self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close()


class PCIEChnlUItf(BaseChnlUItf):
    def __init__(self):
        self.xdma = Xdma()
        self.board = None
        self.open_flag = False

    def accept(self, board, **kwargs):
        if not self.open_flag:
            self.board = board
            self.open_board()

    def open_board(self):
        if not self.open_flag and self.board:
            self.xdma.open_board(self.board)
            self.open_flag = True

    def close_board(self):
        if self.open_flag:
            self.xdma.close_board(self.board)
            self.open_flag = False

    def alloc_buffer(self, length, buf: int = None):
        if self.open_flag:
            return self.xdma.alloc_buffer(self.board, length, buf)

    def free_buffer(self, fd):
        return self.xdma.free_buffer(fd)

    def get_buffer(self, fd, length):
        return self.xdma.get_buffer(fd, length)

    def send_open(self, chnl, fd, length, offset=0):
        if self.open_flag:
            return self.xdma.fpga_send(self.board, chnl, fd, length, offset=offset)

    def recv_open(self, chnl, fd, length, offset=0):
        if self.open_flag:
            return self.xdma.fpga_recv(self.board, chnl, fd, length, offset=offset)

    def wait_dma(self, fd, timeout: int = 0):
        return self.xdma.wait_dma(fd, timeout)

    def break_dma(self, fd):
        return self.xdma.break_dma(fd=fd)

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        if self.open_flag:
            return self.xdma.stream_read(self.board, chnl, fd, length, offset, stop_event, time_out, flag)

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        if self.open_flag:
            return self.xdma.stream_write(self.board, chnl, fd, length, offset, stop_event, time_out, flag)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close_board()
