from typing import TYPE_CHECKING

from .middleware.icd_parser import ICDRegMw
from .middleware.virtual_chnl import VirtualChnlMw

if TYPE_CHECKING:
    from .interface.base import UInterfaceMeta, UInterface, BaseChnlUItf, BaseCmdUItf
    from .middleware.base import UMiddlewareMeta, BaseRegMw, BaseChnlMw


class NSUKit:
    CmdMiddleware: "UMiddlewareMeta" = ICDRegMw
    ChnlMiddleware: "UMiddlewareMeta" = VirtualChnlMw

    def __init__(self, cmd_itf_class: "UInterfaceMeta" = None, chnl_itf_class: "UInterfaceMeta" = None):
        """!
        >>> from nsukit import NSUKit, TCPCmdUItf, PCIECmdUItf
        >>> nsukit = NSUKit(TCPCmdUItf, PCIECmdUItf)
        >>> ...

        @param cmd_itf_class: 指令类
        @param chnl_itf_class: 通道类
        """
        if cmd_itf_class is None or chnl_itf_class is None:
            raise RuntimeError(f'Please pass in a subclass of the {UInterface}')
        self.itf_cmd: "BaseCmdUItf" = cmd_itf_class()
        self.itf_chnl: "BaseChnlUItf" = chnl_itf_class()
        self.mw_cmd: "BaseRegMw" = self.CmdMiddleware(self)
        self.mw_chnl: "BaseChnlMw" = self.ChnlMiddleware(self)

    def start_command(self, target=None, **kwargs) -> None:
        """!
        开启指令

        >>> from nsukit import NSUKit, TCPCmdUItf, PCIECmdUItf
        >>> nsukit = NSUKit(TCPCmdUItf, PCIECmdUItf)
        >>> nsukit.start_command('127.0.0.1', icd_path='~/icd.json')
        >>> print(nsukit.read('dds0中心频率'))
        >>> print(nsukit.read(0x00000000))
        >>> print(nsukit.bulk_read(['dds0中心频率', 0x00000004, 0x00000008]))

        @param target:
        @param kwargs:
        @return:
        """
        self.itf_cmd.accept(target, **kwargs)
        self.mw_cmd.config(**kwargs)

    def stop_command(self) -> None:
        self.itf_cmd.close()

    def write(self, addr, value, execute=True) -> "list | int":
        if isinstance(addr, str):
            self.mw_cmd.set_param(param_name=addr, value=value)
            if execute:
                return self.mw_cmd.find_command(addr)
        else:
            return self.itf_cmd.write(addr, value)

    def read(self, addr) -> int:
        if isinstance(addr, str):
            return self.mw_cmd.get_param(addr)
        else:
            return self.itf_cmd.read(addr)

    def bulk_write(self, params: dict) -> list:
        send_len = []
        for param in params:
            if isinstance(param, str):
                send_len.append(self.write(param, params.get(param)))
            else:
                send_len.append(self.itf_cmd.write(param, params.get(param)))
        return send_len

    def bulk_read(self, addrs: list) -> list:
        value = []
        for addr in addrs:
            value.append(self.read(addr))
        return value

    def start_stream(self, target=None, **kwargs):
        self.itf_chnl.accept(target, **kwargs)
        self.itf_chnl.open_board()
        self.mw_chnl.config(**kwargs)

    def stop_stream(self):
        self.itf_chnl.close()

    def alloc_buffer(self, length, buf: int = None):
        return self.itf_chnl.alloc_buffer(length, buf)

    def free_buffer(self, fd):
        return self.itf_chnl.free_buffer(fd)

    def get_buffer(self, fd, length):
        return self.itf_chnl.get_buffer(fd, length)

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        return self.itf_chnl.stream_read(chnl, fd, length, offset, stop_event, flag)

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        return self.itf_chnl.stream_send(chnl, fd, length, offset, stop_event, flag)

    def send_open(self, chnl, prt, dma_num, length, offset=0):
        return self.itf_chnl.send_open(chnl, prt, dma_num, length, offset)

    def recv_open(self, chnl, prt, dma_num, length, offset=0):
        return self.itf_chnl.recv_open(chnl, prt, dma_num, length, offset)

    def wait_dma(self, fd, timeout: int = 0):
        return self.itf_chnl.wait_dma(fd, timeout)

    def break_dma(self, fd):
        return self.itf_chnl.break_dma(fd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_stream()
        self.stop_command()
