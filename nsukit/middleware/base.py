# Copyright (c) [2023] [Mulan PSL v2]
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
    from .. import NSUKit


class UMiddlewareMeta(type):
    ...


class UMiddleware(metaclass=UMiddlewareMeta):
    def __init__(self, kit: "NSUKit", *args, **kwargs):
        self.kit = kit

    def config(self, **kwargs):
        """!
        可调用此方法配置Middleware里的各种参数，
        会在NSUKit.start_command中调用
        @param args:
        @param kwargs:
        @return:
        """
        ...


class BaseRegMw(UMiddleware):
    def get_param(self, param_name: str, default=0, fmt_type=int):
        ...

    def set_param(self, param_name: str, value, fmt_type=int):
        ...

    def fmt_command(self, command_name, command_type: str = "send", file_name=None) -> bytes:
        ...

    def execute_icd_command(self, parm_name: str) -> list:
        ...

    def param_is_command(self, parm_name: str) -> bool:
        ...


class BaseChnlMw(UMiddleware):
    def alloc_buffer(self, length, buf: int = None):
        ...

    def free_buffer(self, fd):
        ...

    def get_buffer(self, fd, length):
        ...

    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, flag=1) -> bool:
        ...

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1) -> bool:
        ...
