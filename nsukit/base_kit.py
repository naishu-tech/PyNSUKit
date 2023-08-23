from typing import TYPE_CHECKING

from .middleware.icd_parser import ICDRegMw
from .middleware.virtual_chnl import VirtualChnlMw

if TYPE_CHECKING:
    from .interface.base import UInterfaceMeta, UInterface, BaseChnlUItf, BaseCmdUItf
    from .middleware.base import UMiddlewareMeta, BaseRegMw, BaseChnlMw


class KitMeta(type):
    ...


class NSUKit(metaclass=KitMeta):
    """!
    @brief 控制设备的快速开发接口
    @details 该接口支持向设备发送TCP、Serial、PCIE指令，并同时支持TCP、PCIE数据流的上下行。
    """
    CmdMiddleware: "UMiddlewareMeta" = ICDRegMw
    ChnlMiddleware: "UMiddlewareMeta" = VirtualChnlMw

    def __init__(self, cmd_itf_class: "UInterfaceMeta" = None, chnl_itf_class: "UInterfaceMeta" = None):
        """!
        @code
        >>> from nsukit import NSUKit, TCPCmdUItf, PCIECmdUItf
        >>> nsukit = NSUKit(TCPCmdUItf, PCIECmdUItf)
        >>> ...
        @endcode

        @brief 初始化接口
        @details 根据传入的指令接口和数据流接口进行初始化
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
        @code
        >>> from nsukit import NSUKit, TCPCmdUItf, PCIECmdUItf
        >>> nsukit = NSUKit(TCPCmdUItf, PCIECmdUItf)
        >>> nsukit.start_command('127.0.0.1', icd_path='~/icd.json')
        >>> print(nsukit.read('dds0中心频率'))
        >>> print(nsukit.read(0x00000000))
        >>> print(nsukit.bulk_read(['dds0中心频率', 0x00000004, 0x00000008]))
        @endcode

        @brief 发送指令前准备
        @details 根据目标设备类型、参数建立链接
        @param target: 目标设备
        @param kwargs: 其他参数
        @return:
        """
        self.itf_cmd.accept(target, **kwargs)
        # 默认check_recv_head = False
        self.mw_cmd.config(**kwargs)

    def stop_command(self) -> None:
        """!
        @brief 断开链接
        @details 断开当前指令类的链接
        @return:
        """
        self.itf_cmd.close()

    def write(self, addr, value, execute=True) -> "list | int":
        """!
        @brief 写寄存器
        @details 按照输入的地址、值进行写寄存器
        @param addr: 寄存器地址
        @param value: 要写入的值
        @param execute: 是否执行icd指令
        @return: 写入结果
        """
        if isinstance(addr, str):
            if not self.mw_cmd.param_is_command(addr):
                self.mw_cmd.set_param(param_name=addr, value=value)
            if execute:
                return self.mw_cmd.execute_icd_command(addr)
        else:
            return self.itf_cmd.write(addr, value)

    def read(self, addr) -> int:
        """!
        @brief 读寄存器
        @details 按照输入的地址、值进行读寄存器
        @param addr: 寄存器地址
        @return: 读出的值
        """
        if isinstance(addr, str):
            return self.mw_cmd.get_param(addr)
        else:
            return self.itf_cmd.read(addr)

    def bulk_write(self, params: dict) -> list:
        """!
        @brief 批量写寄存器
        @details 按照输入的参数字典以地址、值的方式进行批量写寄存器
        @param params: 参数字典 {key:value,key:value}
        @return: 每个指令的发送长度 [int, int, int]
        """
        send_len = []
        for param in params:
            if isinstance(param, str):
                send_len.append(self.write(param, params.get(param)))
            else:
                send_len.append(self.itf_cmd.write(param, params.get(param)))
        return send_len

    def bulk_read(self, addrs: list) -> list:
        """!
        @brief 批量读寄存器
        @details 按照输入的参数列表批量读取寄存器
        @param addrs: 地址列表
        @return: 每个指令的返回值 [value, value, value]
        """
        value = []
        for addr in addrs:
            value.append(self.read(addr))
        return value

    def start_stream(self, target=None, **kwargs):
        """!
        @brief 开启数据流之前准备
        @details 根据目标设备类型、参数建立链接
        @param target: 目标设备
        @param kwargs: 其他参数
        @return:
        """
        self.itf_chnl.accept(target, **kwargs)
        self.itf_chnl.open_board()
        self.mw_chnl.config(**kwargs)

    def stop_stream(self):
        """!
        @brief 断开链接
        @details 断开当前数据类的链接
        @return:
        """
        self.itf_chnl.close()

    def alloc_buffer(self, length, buf: int = None):
        """!
        @brief 申请一块内存
        @details 根据传入参数开辟一块内存
        @param length: 内存长度
        @param buf: 内存类型
        @return: 内存标号
        """
        return self.itf_chnl.alloc_buffer(length, buf)

    def free_buffer(self, fd):
        """!
        @brief 释放内存
        @details 根据内存标号释放内存
        @param fd: 内存标号
        @return: True/False
        """
        return self.itf_chnl.free_buffer(fd)

    def get_buffer(self, fd, length):
        """!
        @brief 获取内存中的值
        @details 根据内存的key获取内存中存储的数据
        @param fd: 内存地址
        @param length: 获取长度
        @return: 内存中存储的数据
        """
        return self.itf_chnl.get_buffer(fd, length)

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        """!
        @brief 封装好的数据流上行函数
        @details 预封装好的上行函数，将数据写入内存中
        @param chnl: 通道号
        @param fd: 内存表示
        @param length: 上行数据大小
        @param offset: 内存偏移量
        @param stop_event: 外部停止信号
        @param flag:
        @return: True/False
        """
        return self.itf_chnl.stream_recv(chnl, fd, length, offset, stop_event, flag=flag)

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        """!
        @brief 封装好的数据流下行函数
        @details 预封装好的下行函数
        @param chnl: 通道号
        @param fd: 内存表示
        @param length: 上行数据大小
        @param offset: 内存偏移量
        @param stop_event: 外部停止信号
        @param flag:
        @return: True/False
        """
        return self.itf_chnl.stream_send(chnl, fd, length, offset, stop_event, flag)

    def send_open(self, chnl, fd, length, offset=0):
        """!
        @brief 数据下行开启
        @details 开启数据流下行
        @param chnl 未使用
        @param fd 内存标号
        @param length 要发送数据的长度
        @param offset 内存偏移量
        @return
        """
        return self.itf_chnl.send_open(chnl, fd, length, offset)

    def recv_open(self, chnl, fd, length, offset=0):
        """!
        @brief 数据上行开启
        @details 开启数据流上行
        @param chnl
        @param fd 内存标号
        @param length 要接收数据的长度
        @param offset 内存偏移量
        @return True/False
        """
        return self.itf_chnl.recv_open(chnl, fd, length, offset)

    def wait_dma(self, fd, timeout: int = 0):
        """!
        @brief 等待完成一次dma操作
        @details 等待所有数据写入内存
        @param fd 内存标号
        @param timeout 超时时间
        @return 已经写入内存中数据的大小
        """
        return self.itf_chnl.wait_dma(fd, timeout)

    def break_dma(self, fd):
        """!
        @brief 终止本次dma操作
        @details 停止向内存中写入数据
        @param fd 内存标号(key)
        @return 已经写入内存中数据的大小
        """
        return self.itf_chnl.break_dma(fd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_stream()
        self.stop_command()
