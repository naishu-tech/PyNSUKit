import ctypes
import platform
import numpy as np
import os
TIMEOUT = 0xffffffff  # 无限等待

isWindows = False
libxdma = None

if platform.system() == "Linux":
    libxdma = ctypes.CDLL(f"{os.path.dirname(os.path.abspath(__file__))}/libxdma_api.so")
elif platform.system() == "Windows":
    isWindows = True
    libxdma = ctypes.WinDLL(f"{os.path.dirname(os.path.abspath(__file__))}/xdma_api.dll")
    libxdma.fpga_recv_multiple.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint,
                                           ctypes.c_ulonglong,
                                           ctypes.c_ulonglong, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                                           ctypes.c_int]
    libxdma.fpga_recv_multiple.restype = ctypes.c_ulonglong
else:
    pass

assert libxdma, "启动失败"

libxdma.fpga_info_string.argtypes = [ctypes.c_uint]
libxdma.fpga_open.argtypes = [ctypes.c_uint, ctypes.c_uint]
libxdma.fpga_close.argtypes = [ctypes.c_uint]
libxdma.fpga_alloc_dma.argtypes = [ctypes.c_uint, ctypes.c_ulonglong, ctypes.c_void_p, ctypes.c_void_p]
libxdma.fpga_get_dma_buffer.argtypes = [ctypes.c_void_p]
libxdma.fpga_free_dma.argtypes = [ctypes.c_void_p]
libxdma.fpga_send.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_ulonglong,
                              ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_int]
libxdma.fpga_recv.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_ulonglong, ctypes.c_ulonglong,
                              ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_int]

libxdma.fpga_wait_dma.argtypes = [ctypes.c_void_p, ctypes.c_int]
libxdma.fpga_poll_dma.argtypes = [ctypes.c_void_p]
libxdma.fpga_break_dma.argtypes = [ctypes.c_void_p]
libxdma.fpga_wr_lite.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
libxdma.fpga_rd_lite.argtypes = [ctypes.c_uint, ctypes.c_uint]
libxdma.fpga_wait_irq.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_int]
libxdma.fpga_get_dma_speed.argtypes = [ctypes.c_void_p]
libxdma.fpga_debug_dma_regs.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_char_p]
libxdma.fpga_debug_int_regs.argtypes = [ctypes.c_uint, ctypes.c_char_p]


libxdma.fpga_open.restype = ctypes.c_bool
libxdma.fpga_alloc_dma.restype = ctypes.c_void_p
libxdma.fpga_get_dma_buffer.restype = ctypes.c_void_p
libxdma.fpga_send.restype = ctypes.c_ulonglong
libxdma.fpga_recv.restype = ctypes.c_ulonglong
libxdma.fpga_wait_dma.restype = ctypes.c_ulonglong
libxdma.fpga_poll_dma.restype = ctypes.c_ulonglong
libxdma.fpga_break_dma.restype = ctypes.c_ulonglong
libxdma.fpga_rd_lite.restype = ctypes.c_uint
libxdma.fpga_wait_irq.restype = ctypes.c_uint
libxdma.fpga_err_msg.restype = ctypes.c_char_p
libxdma.fpga_get_dma_speed.restype = ctypes.c_double
libxdma.fpga_info_string.restype = ctypes.c_char_p


def fpga_info_string(board):
    return libxdma.fpga_info_string(board).decode()


def fpga_open(board, poll_interval_ms=0):
    return libxdma.fpga_open(board, poll_interval_ms)


def fpga_close(board):
    libxdma.fpga_close(board)


def fpga_alloc_dma(board, length, buf=None, share_buffer=None):
    return libxdma.fpga_alloc_dma(board, length, buf, share_buffer)


def fpga_get_dma_buffer(fd, length):
    return np.frombuffer((ctypes.c_uint * length).from_address(libxdma.fpga_get_dma_buffer(fd)), dtype='u4')


def fpga_free_dma(fd):
    libxdma.fpga_free_dma(fd)


def fpga_send(board, chnl, fd, length, offset=0, last=1, mm_addr=0, mm_addr_inc=0, timeout=TIMEOUT):
    return libxdma.fpga_send(board, chnl, fd, length, offset, last, mm_addr, mm_addr_inc, timeout)


def fpga_recv(board, chnl, fd, length, offset=0, last=1, mm_addr=0, mm_addr_inc=0, timeout=TIMEOUT):
    return libxdma.fpga_recv(board, chnl, fd, length, offset, last, mm_addr, mm_addr_inc, timeout)


# this is for windows only
def fpga_recv_multiple(board, chnl, dma_arr, dma_num, length, offset=0, last=1, mm_addr=0, mm_addr_inc=0, timeout=TIMEOUT):
    return libxdma.fpga_recv_multiple(board, chnl, dma_arr, dma_num, length, offset, last, mm_addr, mm_addr_inc, timeout)


def fpga_wait_dma(fd, timeout=TIMEOUT):
    return libxdma.fpga_wait_dma(fd, timeout)


def fpga_poll_dma(fd):
    return libxdma.fpga_poll_dma(fd)


def fpga_break_dma(fd):
    return libxdma.fpga_break_dma(fd)


def fpga_wr_lite(board, addr, data):
    libxdma.fpga_wr_lite(board, addr, data)


def fpga_rd_lite(board, addr):
    return libxdma.fpga_rd_lite(board, addr)


def fpga_wait_irq(board, num, timeout):
    return libxdma.fpga_wait_irq(board, num, timeout)


def fpga_err_msg():
    return libxdma.fpga_err_msg()


def fpga_get_dma_speed(fd):
    return libxdma.fpga_get_dma_speed(fd)


def fpga_debug_dma_regs(board, chnl):
    sd = ctypes.create_string_buffer(256)
    libxdma.fpga_debug_dma_regs(board, chnl, 1, sd)
    return sd.value


def fpga_debug_int_regs(board):
    sd = ctypes.create_string_buffer(256)
    libxdma.fpga_debug_int_regs(board, sd)
    return sd.value

