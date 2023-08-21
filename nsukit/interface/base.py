import struct


class UInterfaceMeta(type):
    ...


class UInterface(metaclass=UInterfaceMeta):
    def accept(self, *args, **kwargs):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.accept.__name__} method')

    def close(self):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.close.__name__} method')

    def set_timeout(self, s: int):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.set_timeout.__name__} method')


class RegOperationMixin:
    """!

    """
    def reg_write(self, addr, value) -> bool:
        ...

    def reg_read(self, addr) -> int:
        ...


class BaseCmdUItf(UInterface):
    @staticmethod
    def _fmt_reg_write(reg: int = 0, value: bytes = b'') -> bytes:
        """!
        @brief 格式化TCP/serial模拟写寄存器功能的icd
        @param reg: 寄存器地址
        @param value: 寄存器值
        @return 格式化好的icd指令
        """
        if not isinstance(value, bytes):
            raise RuntimeError("The value not be pack")
        pack = (0x5F5F5F5F, 0x31001000, 0x00000000, 24, reg)
        send_cmd = struct.pack('=IIIII', *pack)
        send_cmd += value
        return send_cmd

    @staticmethod
    def _fmt_reg_read(reg: int = 0) -> bytes:
        """!
        @brief 格式化TCP/serial模拟读寄存器功能的icd
        @param reg: 寄存器地址
        @return 格式化好的icd指令
        """
        pack = (0x5F5F5F5F, 0x31001001, 0x00000000, 20, reg)
        return struct.pack('=IIIII', *pack)

    def send_bytes(self, data):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.send_bytes.__name__} method')

    def recv_bytes(self, size):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.recv_bytes.__name__} method')

    def write(self, addr, value):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.write.__name__} method')

    def read(self, addr):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.read.__name__} method')


class BaseChnlUItf(UInterface):
    def open_board(self):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.open_board.__name__} method')

    def close_board(self):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.close_board.__name__} method')

    def alloc_buffer(self, length, buf: int = None):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.alloc_buffer.__name__} method')

    def free_buffer(self, fd):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.free_buffer.__name__} method')

    def get_buffer(self, fd, length):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.get_buffer.__name__} method')

    def send_open(self, chnl, fd, length, offset=0):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.send_open.__name__} method')

    def recv_open(self, chnl, fd, length, offset=0):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.recv_open.__name__} method')

    def wait_dma(self, fd, timeout: int = 0):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.wait_dma.__name__} method')

    def break_dma(self, fd):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.break_dma.__name__} method')

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.stream_read.__name__} method')

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5,  flag=1):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.stream_send.__name__} method')
