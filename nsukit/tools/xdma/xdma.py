#! /usr/bin/python3
# -*- coding:utf-8 -*-
# Copyright (c) [2023] [NaiShu]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

############################
###PCSN, PCIe SRIO Network API Function
###writer: tony
###Date: Dec. 10, 2018
############################

from . import xdma_base
from nsukit.tools.logging import logging
import time
from threading import Lock
TIMEOUT = 1000
TIMEOUT_FLAG = TIMEOUT / 1000 - 1e-3
FAIL = 0xffffffffffffffff

ADDR_RST = 0x00000

RST_GLOBAL_RSTN = 4 * 0x0


class Xdma(object):
    isWindows = xdma_base.isWindows
    function_map = {
        0: [xdma_base.fpga_send, lambda x: x],
        1: [xdma_base.fpga_recv]
    }
    opened_board = {}
    lock = Lock()

    def __init__(self):
        self.board_set = set()
        self.board_info = ""

    def get_info(self, board=0):
        try:
            return xdma_base.fpga_info_string(board)
        except Exception as e:
            logging.error(msg=e)
            return ""
    """
    开启板卡
    """
    def open_board(self, board, poll_interval_ms=0):
        try:
            with self.lock:
                if board in self.opened_board:
                    self.opened_board[board] += 1
                    result = True
                else:
                    self.opened_board[board] = 1
                    result = xdma_base.fpga_open(board, poll_interval_ms)
                print(f'正在打开{self.opened_board[board]=}')
            if not result:
                logging.warning(msg=xdma_base.fpga_err_msg())
            return result
        except Exception as e:
            logging.error(msg=e)

    @staticmethod
    def enable_dma_reg_verify(board):
        try:
            result = xdma_base.fpga_enable_dma_reg_verify(board)
            if not result:
                logging.warning(msg=xdma_base.fpga_err_msg())
            return result
        except Exception as e:
            logging.error(msg=e)

    def close_board(self, board):
        try:
            # getattr(self, "free_pscn_buffer", str)(board)
            with self.lock:
                if board not in self.opened_board:
                    return True
                self.opened_board[board] -= 1
                print(f'正在关闭{self.opened_board[board]=}')
                if self.opened_board[board] == 0:
                    xdma_base.fpga_close(board)
                    self.opened_board.pop(board)
            return True
        except Exception as e:
            logging.error(msg=e)

    # 申请内存
    def alloc_buffer(self, board, length, buf: int = None):
        try:
            fd = xdma_base.fpga_alloc_dma(board, length, buf=buf)
            assert fd, f"板卡{board}内存申请失败"
            return fd
        except Exception as e:
            logging.error(msg=e)
            logging.warning(msg=xdma_base.fpga_err_msg())
            return False

    # 获取内存
    @staticmethod
    def get_buffer(fd, length):
        try:
            return xdma_base.fpga_get_dma_buffer(fd, length)
        except Exception as e:
            logging.error(msg=f"获取内存失败, {e}")
            logging.warning(msg=xdma_base.fpga_err_msg())
            return False

    def free_buffer(self, fd):
        try:
            xdma_base.fpga_free_dma(fd)
            return True
        except Exception as e:
            logging.error(msg=e)
            logging.warning(msg=xdma_base.fpga_err_msg())
            return False

    """
    寄存器写入
        参数： fdindex：fpga_id; addr: address; data: data; timeout: by millisecond 
        返回值：True/False
    """

    @staticmethod
    def alite_write(addr, data, board=0):
        try:
            xdma_base.fpga_wr_lite(board, addr, data)
            return True
        except Exception as e:
            logging.error(msg=e)
            logging.warning(msg=xdma_base.fpga_err_msg())
            return False

    """
    寄存器读出
        参数：fdindex: fpga_id; addr: address; timeout: by millisecond
        返回值：[True/False, rddata]
    """

    @staticmethod
    def alite_read(addr, board=0, _=None):
        try:
            value = xdma_base.fpga_rd_lite(board, addr)
            if value == -1:
                logging.warning(msg=xdma_base.fpga_err_msg())
                return False, 0
            return True, value
        except Exception as e:
            logging.error(msg=e)
            return False, 0

    @staticmethod
    def wait_irq(idx, board, timeout=0):
        try:
            xdma_base.fpga_wait_irq(board, idx, timeout)
            return 1
        except Exception as e:
            logging.error(msg=e)
            return 0

    """
    复位主节点
        返回值：True/False
    """

    def reset_board(self, board):
        try:
            self.alite_write(ADDR_RST + RST_GLOBAL_RSTN, 0, board)
            time.sleep(1e-3)
            self.alite_write(ADDR_RST + RST_GLOBAL_RSTN, 1, board)
            return True
        except Exception as e:
            logging.error(msg=e)
            return False

    """
    数据流写入
        返回值：True/False
    """
    def stream_read(self, board, chnl, fd, length, offset=0, stop_event=None, time_out=5,  flag=1):
        prt = fd
        function = xdma_base.fpga_recv
        return self.stream_public(board, chnl, prt, fd, length, function, offset, stop_event, time_out, flag)

    """
    数据流读出
        返回值：True/False
    """

    def stream_write(self, board, chnl, fd, length, offset=0, stop_event=None, time_out=5,  flag=1):
        return self.stream_public(board, chnl, fd, fd, length, xdma_base.fpga_send, offset, stop_event, time_out, flag)

    def stream_public(self, board, chnl, prt, fd, length, function, offset, stop_event, time_out, flag):
        try:
            recv = function(board, chnl, prt, length, offset=offset, timeout=0)
            return self.__check_buffer(recv, board, chnl, fd, length, stop_event, time_out, flag)
        except Exception as e:
            logging.error(msg=e)
            return False

    def __check_buffer(self, recv, board, chnl, fd, length, stop_event, time_out, flag):
        try:
            if recv == FAIL:
                logging.error(msg=xdma_base.fpga_err_msg())
                return False
            else:
                cnt = 1
                if not stop_event:
                    stop_event = self._stop_event
                recv_total = 0
                while length != recv_total:
                    if stop_event():
                        xdma_base.fpga_break_dma(fd)
                        break
                    st = time.time()
                    recv_total = xdma_base.fpga_wait_dma(fd, timeout=time_out)
                    diff_time = time.time() - st
                    if flag and cnt and diff_time > TIMEOUT_FLAG:
                        # xdma超时打印
                        # logging.debug(msg=xdma_base.fpga_err_msg())
                        # logging.debug(msg=xdma_base.fpga_debug_dma_regs(board, chnl))
                        # logging.debug(msg=xdma_base.fpga_debug_int_regs(board))
                        # logging.debug(msg=f'xdma超时: {diff_time}')
                        cnt -= 1
                return True
        except Exception as e:
            logging.error(msg=e)
            return False

    @staticmethod
    def _stop_event():
        return False

    def fpga_send(self, board, chnl, prt, length, offset=0):
        return xdma_base.fpga_send(board, chnl, prt, length, offset=offset, timeout=0)

    def fpga_recv(self, board, chnl, prt, length, offset=0):
        return xdma_base.fpga_recv(board, chnl, prt, length, offset=offset, timeout=0)

    def wait_dma(self, fd, timeout=0):
        if timeout:
            return xdma_base.fpga_wait_dma(fd, timeout=TIMEOUT)
        else:
            return xdma_base.fpga_wait_dma(fd, timeout=timeout)

    def break_dma(self, fd):
        return xdma_base.fpga_break_dma(fd=fd)
