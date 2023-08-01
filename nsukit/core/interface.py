from dataclasses import dataclass, field
import socket
import struct
import threading
import time
import numpy as np
import serial
from typing import Union
from threading import Lock, Event
# from .xdma import xdma_sim as xdma
from .xdma import xdma as xdma
from ..tools.logging import logging


class CmdInterfaceBusy(RuntimeError):
    def __str__(self):
        return f'{self.__class__.__name__}: {self.args[0]}'


class Interface:

    @staticmethod
    def _fmt_reg_cmd(reg: int = 0, value: int = 0, mode=1) -> bytes:
        if mode:
            pack = [0x5F5F5F5F, 0x31000000, 0x00000000, 24, reg, value]
            return struct.pack('=IIIIII', *pack)
        else:
            pack = [0x5F5F5F5F, 0x31000000, 0x00000000, 24, reg]
            return struct.pack('=IIIII', *pack)

    def accept(self):
        pass

    def close(self):
        pass

    def send_bytes(self, data):
        pass

    def recv_bytes(self, size):
        pass

    def write(self, addr, value):
        pass

    def read(self, addr):
        pass

    def set_timeout(self, s: int):
        pass


class CommandTCP(Interface):
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

        :param target_id: IP地址
        :param args:
        :return:
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

        :param size: 返回长度
        :return:
        """
        with self.busy_lock:
            return self._tcp_server.recv(size)

    def send_bytes(self, data: bytes) -> int:
        """

        :param data: 数据
        :return: 已发送的长度
        """
        with self.busy_lock:
            send_len = self._tcp_server.send(data)
            return send_len

    def write(self, addr: int, value: int) -> int:
        cmd = self._fmt_reg_cmd(addr, value)
        return self.send_bytes(cmd)

    def read(self, addr: int) -> int:
        cmd = self._fmt_reg_cmd(addr, mode=0)
        return self.send_bytes(cmd)

    def close(self):
        try:
            self._tcp_server.shutdown(socket.SHUT_RDWR)
            self._tcp_server.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, s: int = 5):
        """

        :param s: 时间（秒）
        :return:
        """
        self._tcp_server.settimeout(s)

    def get_number(self):
        return self._serial_num

    def update_number(self):
        self._serial_num += 1


class CommandSerial(Interface):
    _target_id = 'COM0'
    _target_baud_rate = 9600
    _timeout = 5

    def __init__(self):
        """
        串口指令收发接口

        """
        self._device_serial = None
        self.busy_lock = Lock()

    def accept(self, target_id=None, *args):
        _target_id = self._target_id if target_id is None else target_id
        with self.busy_lock:
            if self._device_serial is not None:
                self._device_serial.close()
            if args:
                self._device_serial = serial.Serial(target_id, *args)
            else:
                self._device_serial = serial.Serial(port=_target_id,
                                                    baudrate=int(self._target_baud_rate),
                                                    timeout=self._timeout)

    def recv_bytes(self, size: int = 1024) -> bytes:
        """

        :param size:
        :return:
        """
        with self.busy_lock:
            return self._device_serial.read(size)

    def send_bytes(self, data: bytes):
        with self.busy_lock:
            return self._device_serial.write(data)

    def write(self, addr: int, value: int) -> int:
        cmd = self._fmt_reg_cmd(addr, value)
        return self.send_bytes(cmd)

    def read(self, addr: int | str):
        cmd = self._fmt_reg_cmd(addr, mode=0)
        return self.send_bytes(cmd)

    def close(self):
        try:
            self._device_serial.close()
        except Exception as e:
            logging.error(msg=e)

    def set_timeout(self, value):
        self._device_serial.timeout = value


class CommandPCIE(Interface):
    _once_send_or_recv_timeout = 1  # _break_status状态改变间隔应超过该值
    _timeout = 30
    _block_size = 4096
    _break_status = bool
    ADDR_SENT_DOWN = 48 * (1024 ** 2) // 4 - 1
    lock = Lock()
    irq_num = 15

    def __init__(self):
        self.board = 0
        self.xdma = xdma.Xdma()
        self.timeout = self._timeout
        self.sent_base = 0
        self.recv_base = 0
        self.sent_ptr = 0
        self.recv_ptr = 0
        self.recv_event = Event()
        self.open_flag = False

    def open_board(self):
        if not self.open_flag:
            self.xdma.open_board(self.board)
            self.open_flag = True

    def close_board(self):
        if self.open_flag:
            self.xdma.close_board(self.board)
            self.open_flag = False

    def accept(self, board: int = 0, sent_base=0, recv_base=0):
        """

        :param board: board number
        :param sent_base:
        :param recv_base:
        :return:
        """
        self.board = board
        self.sent_base = sent_base
        self.recv_base = recv_base
        self.open_board()

    def close(self):
        self.lock.release()

    def settimeout(self, s: int):
        """

        :param s: second
        :return:
        """
        self.timeout = s

    def write(self, addr: int, value: int):
        if self.open_flag:
            self.xdma.alite_write(addr, value, self.board)

    def read(self, addr: int):
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
                assert not self._break_status(), "中断指令发送"
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
                assert not self._break_status(), "中断指令接收"
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
            raise TimeoutError(f'toaxi超时')
        if callable(callback):
            callback()
        self.reset_irq()
        self.recv_event.set()

    @classmethod
    def get_service(cls, board, pscn, sent_base, recv_base, timeout=None, _break_status=None):
        try:
            assert timeout is None or (isinstance(timeout, (int, float)) and timeout >= 0), f"非法的timeout({timeout})"
            self = cls(board, pscn, sent_base, recv_base)
            if callable(_break_status):
                setattr(self, "_break_status", _break_status)
            # x and y 的值, x为真就是y, x为假就是x
            self.settimeout(timeout)
            return self
        except Exception as e:
            return f"{e}"

    def __enter__(self):
        self.lock.acquire(timeout=self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()
        if self.open_flag:
            self.close_board()


class DataTCP(Interface):
    _local_port = 6001
    _timeout = None
    DISCONNECT = 0

    @dataclass
    class Memory:
        memory: np.ndarray
        memory_size: int
        memory_id: int
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
            logging.info(msg='已建立连接')
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

    def alloc_buffer(self, length, buf: int = None):
        memory_obj = self.Memory(memory=np.zeros(shape=length, dtype='u4'), memory_size=length, memory_id=self.memory_index, in_use=False)
        self.memory_dict[self.memory_index] = memory_obj
        self.memory_index += 1
        return memory_obj.memory_id

    def free_buffer(self, fd):
        return self.memory_dict.pop(fd)

    def get_buffer(self, memory_id: int):
        return self.memory_dict[memory_id].memory

    def send_open(self):
        raise RuntimeError("暂不支持")

    def recv_open(self, memory_id: int):
        pass

    def _recv(self):
        pass

    def wait_dma(self):
        pass

    def break_dma(self):
        pass

    def stream_read(self):
        pass


class DataPCIE(Interface):

    def __init__(self):
        self.xdma = xdma.Xdma()
        self.board = None
        self.open_flag = False

    def accept(self, board: int = 0):
        if not self.open_flag:
            self.board = board
            self.open_board()
            self.open_flag = True

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

    def send_open(self, chnl, prt, dma_num, length, offset=0):
        if self.open_flag:
            return self.xdma.fpga_send(self.board, chnl, prt, dma_num, length, offset=offset)

    def recv_open(self, chnl, prt, dma_num, length, offset=0):
        if self.open_flag:
            return self.xdma.fpga_recv(self.board, chnl, prt, dma_num, length, offset=offset)

    def wait_dma(self, fd, timeout: int = 0):
        return self.xdma.wait_dma(fd, timeout)

    def break_dma(self, fd):
        return self.xdma.break_dma(fd=fd)

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        if self.open_flag:
            return self.xdma.stream_read(self.board, chnl, fd, length, offset, stop_event, flag)

    def stream_send(self):
        raise RuntimeError("暂不支持")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.open_flag:
            self.close_board()
