import struct


class UInterfaceMeta(type):
    ...


class UInterface(metaclass=UInterfaceMeta):
    def accept(self, *args, **kwargs):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.accept.__name__} method')

    def close(self):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.close.__name__} method')

    def send_bytes(self, data):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.send_bytes.__name__} method')

    def recv_bytes(self, size):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.recv_bytes.__name__} method')

    def write(self, addr, value):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.write.__name__} method')

    def read(self, addr):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.read.__name__} method')

    def set_timeout(self, s: int):
        raise NotImplementedError(f'Please overload the {self.__class__.__name__}.{self.set_timeout.__name__} method')


class BaseCmdUItf(UInterface):
    @staticmethod
    def _fmt_reg_write(reg: int = 0, value: int = 0) -> bytes:
        """!
        @brief 格式化TCP/serial模拟写寄存器功能的icd
        @param reg: 寄存器地址
        @param value: 寄存器值
        @return: 格式化好的icd指令
        """
        pack = (0x5F5F5F5F, 0x31000000, 0x00000000, 24, reg, value)
        return struct.pack('=IIIIII', *pack)

    @staticmethod
    def _fmt_reg_read(reg: int = 0) -> bytes:
        """!
        @brief 格式化TCP/serial模拟读寄存器功能的icd
        @param reg: 寄存器地址
        @return: 格式化好的icd指令
        """
        pack = (0x5F5F5F5F, 0x31000000, 0x00000000, 24, reg)
        return struct.pack('=IIIII', *pack)


class BaseChnlUItf(UInterface):
    def open_board(self):
        ...

    def close_board(self):
        ...

    def alloc_buffer(self, length, buf: int = None):
        ...

    def free_buffer(self, fd):
        ...

    def get_buffer(self, fd, length):
        ...

    def send_open(self, chnl, fd, length, offset=0):
        ...

    def recv_open(self, chnl, fd, length, offset=0):
        ...

    def wait_dma(self, fd, timeout: int = 0):
        ...

    def break_dma(self, fd):
        ...

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        ...

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5,  flag=1):
        ...
