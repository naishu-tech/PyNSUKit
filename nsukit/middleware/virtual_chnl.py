# Copyright (c) [2023] [Mulan PSL v2]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import threading
import time
from enum import Enum
from functools import wraps
from queue import PriorityQueue, Empty
from dataclasses import dataclass
from typing import TYPE_CHECKING, Union, Optional, Dict

from .base import BaseChnlMw
from ..interface.base import RegOperationMixin
from ..tools.logging import logging
from ..tools.xdma.xdma import FAIL

if TYPE_CHECKING:
    from .. import NSUKit
    from ..interface.base import BaseChnlUItf


def dispenser(func):
    """!
    装饰器，让被装饰的函数根据stream_mode将调用分到指定的实现上
    @param func:
    @return:
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        self: "VirtualChnlMw" = args[0]
        if self.stream_mode == self.StreamMode.VIRTUAL:
            _func = func
        else:
            _func = getattr(self.kit.itf_chnl, func.__name__)
        return _func(*args, **kwargs)

    return wrapper


class VirtualChnlMw(BaseChnlMw):
    """!
    按一定规则，从一个物理通道虚拟出若干个虚拟数据通道进行上行
    """
    VCHNL_NUM = 8
    R2V_CHNL = 0
    PARAM_ADDR = 0x00000000
    PARAM_WR_ADDR = 0x00000000
    STATUS_ADDR = 0x00000000

    class StreamMode(str, Enum):
        VIRTUAL = 'virtual'
        REAL = 'real'

    @dataclass
    class ChnlEntry:
        chnl: int
        priority: int

        def __lt__(self, other):
            return self.priority < other.priority

    def __init__(self, kit: "NSUKit"):
        super(VirtualChnlMw, self).__init__(kit)
        self.itf_chnl: "Union[BaseChnlUItf, RegOperationMixin, None]" = None
        self.stream_mode = self.StreamMode.REAL
        self.running_lock = threading.Lock()
        self.cancel_event = threading.Event()
        self.canceled = threading.Event()
        self.priority_lock = threading.Lock()
        self.priority_thread = None
        self.priority_queue = PriorityQueue(maxsize=self.VCHNL_NUM)
        self.priority_chnl: "Dict[int, int]" = {ch: 0 for ch in range(self.VCHNL_NUM)}
        self.priority_events: "Dict[int, threading.Event]" = {ch: threading.Event() for ch in range(self.VCHNL_NUM)}

    def config(self, *, stream_mode='real', **kwargs):
        """!
        配置中间件所使用的数据流模式，是直接转发给对应的Chnl
        @param stream_mode: 可选
        @param kwargs:
        @return:
        """
        self.stream_mode = self.StreamMode(stream_mode)
        self.cancel_event.set()
        if not self.canceled.wait(timeout=10):
            raise RuntimeError(f'stream_mode switch failed')
        self.priority_chnl: "Dict[int, int]" = {ch: 0 for ch in range(self.VCHNL_NUM)}
        self.itf_chnl = None

        if self.stream_mode == self.StreamMode.REAL:
            ...
        elif self.stream_mode == self.StreamMode.VIRTUAL:
            if not isinstance(self.kit.itf_chnl, RegOperationMixin):
                raise ValueError(f'When {stream_mode=} is virtual, '
                                 f'{self.kit.__class__}.itf_chnl should be a subclass of {RegOperationMixin}')
            self.priority_thread = threading.Thread(target=self.priority_wheel, name=f'virtual_chnl', daemon=True)
            self.priority_thread.start()

    @dispenser
    def alloc_buffer(self, length, buf: int = None):
        return self.kit.itf_chnl.alloc_buffer(length, buf)

    @dispenser
    def free_buffer(self, fd):
        return self.kit.itf_chnl.free_buffer(fd)

    @dispenser
    def get_buffer(self, fd, length):
        return self.kit.itf_chnl.get_buffer(fd, length)

    def priority_wheel(self):
        self.canceled.clear()
        while not self.cancel_event.is_set():
            try:
                with self.running_lock:
                    entry: "VirtualChnlMw.ChnlEntry" = self.priority_queue.get(timeout=1)
            except Empty as e:
                continue
            for ch in range(self.VCHNL_NUM):
                if ch == entry.chnl:
                    self.priority_events[ch].set()
                else:
                    self.priority_events[ch].clear()
        self.cancel_event.clear()
        self.canceled.set()

    def register_chnl(self, chnl):
        entry = self.ChnlEntry(chnl, self.priority_chnl[chnl])
        self.priority_queue.put(entry)

    def _priority_lock(self, chnl, stop_event, timeout):
        event = self.priority_events[chnl]
        while not stop_event():
            if event.wait(timeout):
                break
        self.priority_chnl[chnl] += 1

    @dispenser
    def stream_read(self, chnl, fd, length, offset=0, stop_event=None, flag=1, timeout=1) -> bool:
        """!
        使用虚拟通道上行，通道会遵循
        @param chnl:
        @param fd:
        @param length:
        @param offset:
        @param stop_event:
        @param flag:
        @param timeout:
        @return:
        """
        if chnl >= self.VCHNL_NUM:
            raise ValueError(
                f'{chnl=} should not be greater than the maximum number of virtual channels {self.VCHNL_NUM}')
        if not stop_event:
            stop_event = self._stop_event
        self.register_chnl(chnl)
        self._priority_lock(chnl, stop_event, timeout)

        with self.running_lock:
            self.itf_chnl = itf = self.kit.itf_chnl
            try:
                flag = itf.recv_open(self.R2V_CHNL, fd, length=length, offset=offset)
                if flag == FAIL:
                    logging.error(msg=f'VChnl start Fail')
                    return False
                self.v_param = (length, chnl)
                recv_total = 0
                while length != recv_total:
                    if stop_event():
                        itf.break_dma(fd)
                        break
                    recv_total = itf.wait_dma(fd, timeout=timeout)
                residue, valid_ch = self.v_param
                if residue:
                    raise RuntimeError(f'The current virtual channel {chnl}:{valid_ch} still has residual data')
                return True
            except Exception as e:
                logging.error(msg=e)
                return False

    @dispenser
    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
        stream_mode = self.stream_mode
        raise RuntimeError(f'This interface cannot be called when the {stream_mode=}')

    @property
    def v_param(self) -> tuple:
        """!
        status[26:0]: 当前传输剩余的字数（当前位宽的字数）；
        status[29:27]: 当前传输的源通道号，0-7；

        @return: (当前传输剩余的字数, 当前传输的源通道号)
        """
        _v = self.itf_chnl.reg_read(self.STATUS_ADDR)
        return _v & (2 ** 26 - 1), _v >> 26

    @v_param.setter
    def v_param(self, value: tuple):
        """!
        param[26:0]: 本次传输长度（当前位宽的字数）；
        param[29:27]:选通的axis-s端口号，0-7；

        @param value: (本次传输长度, 选通的axis-s端口号)
        @return:
        """
        _param = (value[0] & (2 ** 26 - 1)) + (value[1] << 26)
        self.itf_chnl.reg_write(self.PARAM_ADDR, _param)
        self.itf_chnl.reg_write(self.PARAM_WR_ADDR, 0xFFFFFFFF)
        time.sleep(0.005)
        self.itf_chnl.reg_write(self.PARAM_WR_ADDR, 0)

    @staticmethod
    def _stop_event():
        return False
