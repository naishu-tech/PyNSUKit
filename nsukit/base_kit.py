# Copyright (c) [2023] [Mulan PSL v2]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import enum
from typing import TYPE_CHECKING, Any

import numpy as np

from .middleware.icd_parser import ICDRegMw
from .middleware.virtual_chnl import VirtualChnlMw

if TYPE_CHECKING:
    from .interface import InitParamSet
    from .interface.base import UInterfaceMeta, UInterface, BaseChnlUItf, BaseCmdUItf
    from .middleware.base import UMiddlewareMeta, BaseRegMw, BaseChnlMw


class BulkMode(str, enum.Enum):
    """!
    用于NSUKit.bulk_xxx方法的枚举类

    **LOOP**: 对一个寄存器地址，循环写入/读出指定长度数据

    **INCREMENT**: 对一个从一个寄存器地址开始，依次遍历指定数量的寄存器
    """

    LOOP = 'loop'
    INCREMENT = 'inc'


class KitMeta(type):
    ...


class NSUKit(metaclass=KitMeta):
    """!
    @brief 控制设备的快速开发接口
    @details 该接口支持向设备发送TCP、Serial、PCIE指令，并同时支持TCP、PCIE数据流的上下行。
    """
    CmdMiddleware: "UMiddlewareMeta" = ICDRegMw
    ChnlMiddleware: "UMiddlewareMeta" = VirtualChnlMw

    def __init__(self,
                 cmd_itf_class: "UInterfaceMeta" = None,
                 stream_itf_class: "UInterfaceMeta" = None,
                 cmd_param: "InitParamSet" = None,
                 stream_param: "InitParamSet" = None):
        """!
        @brief 初始化接口
        @details 根据传入的指令接口和数据流接口进行初始化
        @anchor NSUKit_init
        @param cmd_itf_class: 指令类
        @param stream_itf_class: 通道类

        ---
        示例代码如下
        @code
        >>> from nsukit import NSUKit
        >>> from nsukit.interface import TCPCmdUItf, PCIEStreamUItf
        >>> nsukit = NSUKit(TCPCmdUItf, PCIEStreamUItf)
        >>> ...
        @endcode

        """
        if cmd_itf_class is None or stream_itf_class is None:
            raise RuntimeError(f'Please pass in a subclass of the {UInterface}')
        self.itf_cmd: "BaseCmdUItf" = cmd_itf_class()
        self.itf_chnl: "BaseChnlUItf" = stream_itf_class()
        self.mw_cmd: "BaseRegMw" = self.CmdMiddleware(self)
        self.mw_chnl: "BaseChnlMw" = self.ChnlMiddleware(self)

    def link_cmd(self) -> None:
        """!

        @brief 建立cmd连接
        @details 根据初始化时传入的协议类参数，对板卡发起连接，会调用协议类的accept方法
        @anchor NSUKit_link_cmd
        @return: 枚举值NSUKitStatusT中表示的状态
        """
        ...

    def link_stream(self) -> None:
        """!

        @brief 建立stream连接
        @details 根据初始化时传入的数据流协议类参数，对板卡发起连接，会调用数据流协议类的accept方法
        @anchor NSUKit_link_stream
        @return:
        """
        ...

    def unlink_cmd(self):
        """!
        @brief 断开链接
        @details 断开当前cmd协议类的链接
        @return:
        """
        ...

    def unlink_stream(self):
        """!
        @brief 断开链接
        @details 断开当前stream协议类的链接
        @return:
        """
        ...

    def write(self, addr: int, value: bytes) -> None:
        """!
        @brief 写寄存器
        @details 按照输入的地址、值进行写寄存器
        @anchor NSUKit_write
        @param addr: 寄存器地址
        @param value: 要写入的值，为一len为4的bytes对象
        @return: 无返回值，无报错即成功

        ---
        调用示例
        @code
        >>> kit: NSUKit
        >>> kit.write(0x10, b'\x00\x00\x00\x00')
        @endcode

        @code
        >>> kit: NSUKit
        >>> try:
        >>>     kit.write(0x10, b'\x00'*5)
        >>> except Exception as e:
        >>>     print(f'Failed')
        @endcode
        """
        ...

    def read(self, addr: int) -> bytes:
        """!
        @brief 读寄存器
        @details 按照输入的地址进行读寄存器
        @anchor NSUKit_read
        @param addr: 寄存器地址
        @return: 读出的值，为一len为4的bytes对象

        ---
        调用示例
        @code
        >>> kit: NSUKit
        >>> value = kit.read(0x10)
        >>> len(value) == 4
        @endcode
        """
        ...

    def bulk_write(self, base: int, value: bytes, mode: BulkMode = BulkMode.INCREMENT) -> None:
        """!

        @brief 片写寄存器
        @details 按照输入的基地址和指定模式，将数据写入寄存器
        @anchor NSUKit_bulk_write
        @param base: 基寄存器地址
        @param value: 要写入的数据，不限长度
        @param mode: 枚举类型BulkMode中的的值
        @return: None，无报错即成功

        ---
        将基地址0x10的寄存器片，重置为0
        @code
        >>> kit: NSUKit
        >>> kit.bulk_write(0x10, b'\x00'*51)
        @endcode

        通过地址为0x10的寄存器，传输一段周期数据
        @code
        >>> kit: NSUKit
        >>> kit.bulk_write(0x10, b'\x00\x01'*51, mode='inc')
        @endcode
        """
        ...

    def bulk_read(self, base: int, length: int, mode: BulkMode = BulkMode.INCREMENT) -> bytes:
        """!
        @brief 片读寄存器
        @details 按照输入的基地址和指定模式，从寄存器中读出数据
        @anchor NSUKit_bulk_read
        @param base: 基寄存器地址
        @param length: 要片读的数据长度，可为任意长度
        @param mode: 枚举类型BulkMode中的的值
        @return: 读取结果，长度为length指定值

        ---
        从基地址0x10的寄存器开始，依次读回片内寄存器的值
        @code
        >>> kit: NSUKit
        >>> value = kit.bulk_read(0x10, 51)
        >>> len(value) == 51
        @endcode
        """
        ...

    def set_param(self, name: str, value: Any) -> None:
        """!
        设置指令参数值

        **并不会真的下发到设备中，只是把相应的参数值写入到主机内存中**
        @anchor NSUKit_set_param
        @param name: 所有指令中包含的参数名，具体支持的参数可以查阅板卡配套的说明文档
        @param value: 要配置的参数值，支持int、float等值类型，文件路径，numpy.ndarray
        @return: None,执行失败则报错

        ---
        向板卡DAC1中预置一段波形
        @code
        >>> kit: NSUKit
        >>> kit.set_param('DAC预置波形选通', 1)
        >>> kit.set_param('DAC预置波形文件', './freq_1e6_8Gsps_2us.dat')
        >>> kit.execute('波形预置')
        @endcode
        """
        ...

    def get_param(self, name: str) -> Any:
        """!
        获取指令参数值

        **并不会真的从设备中读出，只是把相应的参数值从内存中读出**
        @anchor NSUKit_get_param
        @param name: 参数名
        @return: 主机内存中存储的参数值

        示例:
        @code
        >>> kit: NSUKit
        >>> ref_src = kit.get_param('参考时钟来源')
        @endcode

        ---
        获取板卡核心温度:
        @code
        >>> kit: NSUKit
        >>> kit.execute('状态查询')
        >>> core_temp = kit.get_param('核心温度')
        @endcode
        """
        ...

    def execute(self, cmd: str) -> None:
        """!
        执行指令

        **把set_param配置的参数值打包发给板卡，并将相应的返回参数写入内存**
        @anchor NSUKit_execute
        @param cmd: 指令名
        @return: None,执行失败则报错

        ---
        示例:
        @code
        >>> kit: NSUKit
        >>> kit.execute('RF配置')
        @endcode
        """
        ...

    def alloc_buffer(self, length, buf: int = None) -> int:
        """!
        @brief 申请一块内存
        @details 根据传入参数开辟一块内存
        @anchor NSUKit_alloc_buffer
        @param length: 要申请的内存大小
        @param buf: 外部指定的内存指针
        @return: 经过nsukit修饰过后可用于数据流传输的 **内存标识符fd**
        """
        return self.itf_chnl.alloc_buffer(length, buf)

    def free_buffer(self, fd) -> None:
        """!
        @brief 释放内存
        @details 根据 **内存标识符** 释放内存
        @anchor NSUKit_free_buffer
        @param fd: 内存标识符
        @return: None
        """
        return self.itf_chnl.free_buffer(fd)

    def get_buffer(self, fd, length) -> np.ndarray:
        """!
        @brief 获取内存中的值
        @details 根据内存标识符获取对应内存中存储的数据
        @anchor NSUKit_get_buffer
        @param fd: 内存标识符
        @param length: 要获取的数据长度
        @return: 内存中存储的数据，以numpy.ndarray的形式返回
        """
        return self.itf_chnl.get_buffer(fd, length)

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        """!
        @brief 封装好的数据流上行函数
        @details 预封装好的上行函数，将数据写入内存中
        @anchor NSUKit_stream_recv
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
        @anchor NSUKit_stream_send
        @param chnl: 通道号
        @param fd: 内存表示
        @param length: 上行数据大小
        @param offset: 内存偏移量
        @param stop_event: 外部停止信号
        @param flag:
        @return: True/False
        """
        return self.itf_chnl.stream_send(chnl, fd, length, offset, stop_event, flag)

    def open_send(self, chnl, fd, length, offset=0):
        """!
        @brief 数据下行开启
        @details 开启数据流下行，且不会发生阻塞
        @anchor NSUKit_open_send
        @param chnl 数传通道号
        @param fd 内存标号
        @param length 要发送数据的长度，单位byte
        @param offset 内存偏移量
        @return
        """
        return self.itf_chnl.send_open(chnl, fd, length, offset)

    def open_recv(self, chnl, fd, length, offset=0):
        """!
        @brief 数据上行开启
        @details 开启数据流上行
        @anchor NSUKit_open_recv
        @param chnl
        @param fd 内存标号
        @param length 要接收数据的长度，单位byte
        @param offset 内存偏移量
        @return True/False
        """
        return self.itf_chnl.recv_open(chnl, fd, length, offset)

    def wait_stream(self, fd, timeout: float = 0):
        """!
        @brief 等待完成一次dma操作
        @details 等待所有数据写入内存
        @anchor NSUKit_wait_stream
        @param fd 内存标号
        @param timeout 超时时间
        @return 已经写入内存中数据的大小
        """
        return self.itf_chnl.wait_dma(fd, timeout)

    def break_stream(self, fd):
        """!
        @brief 终止本次dma操作
        @details 停止向内存中写入数据
        @anchor NSUKit_break_stream
        @param fd 内存标号(key)
        @return 已经写入内存中数据的大小
        """
        return self.itf_chnl.break_dma(fd)
