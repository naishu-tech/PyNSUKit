# Copyright (c) [2023] [NaiShu]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .. import NSUSoc
    from ..interface import InitParamSet


class UMiddlewareMeta(type):
    """!
    @note 处理层接口的元类，当前做类型注解用，开发处理层接口时不用关心此类
    """
    ...


class UMiddleware(metaclass=UMiddlewareMeta):
    def __init__(self, kit: "NSUSoc", *args, **kwargs):
        self.kit = kit

    def config(self, param: "InitParamSet") -> None:
        """!
        可调用此方法配置Middleware里的各种参数，
        会在NSUKit.link_command中调用
        @return:
        """
        ...


class BaseRegMw(UMiddleware):
    def get_param(self, param_name: str, default=0, fmt_type=int):
        ...

    def set_param(self, param_name: str, value, fmt_type=int):
        ...

    def execute(self, cname: str) -> None:
        ...

    def fmt_command(self, command_name, command_type: str = "send", file_name=None) -> bytes:
        ...

    def execute_from_pname(self, parm_name: str) -> list:
        ...


class BaseStreamMw(UMiddleware):
    def open_send(self, chnl: int, fd: int, length: int, offset: int = 0):
        ...

    def open_recv(self, chnl: int, fd: int, length: int, offset: int = 0):
        ...

    def wait_stream(self, fd: int, timeout: float = 0):
        ...

    def break_stream(self, fd: int):
        ...

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, flag=1) -> bool:
        ...

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1) -> bool:
        ...
