# Copyright (c) [2023] [NaiShu]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""!
@brief 检查函数集合
@file check_func.py
"""

import collections.abc as abc
import struct
from typing import Union, Iterable


def head_check(send_cmd: bytes, recv_cmd: bytes):
    """!
    @brief 包头检查
    @details 返回数据包头检查
    @param send_cmd 发送的指令
    @param recv_cmd 返回的指令
    @return 返回指令的总长度
    """
    send_head = struct.unpack('=IIII', send_cmd[:16])
    recv_head = struct.unpack('=IIII', recv_cmd[:16])
    if recv_head[0] != 0xCFCFCFCF:
        raise RuntimeError("返回包头错误")
    if recv_head[1] != send_head[1]:
        raise RuntimeError("返回ID错误")
    return recv_head[3]


class InvalidRegisterValueError(ValueError):
    """!
    自定义异常类，用于表示不合法的寄存器值错误
    """
    ...


def check_reg_schema(addr: Union[int, Iterable[int]], value: Union[bytes, Iterable[bytes], None] = None) -> None:
    """!
    检查寄存器地址和值是否合法
    @param addr: 寄存器地址，或寄存器地址列表
    @param value: 寄存器地址或寄存器地址
    @return None
    """
    if isinstance(addr, int) and isinstance(value, bytes):
        if addr < 0:
            raise InvalidRegisterValueError(f'The value of addr should be greater than 0, not {addr=}.')
        if len(value) > 4:
            raise InvalidRegisterValueError(
                f'The length of the value must be less than or equal to 4, not {len(value)=}.')
    elif isinstance(addr, int) and value is None:
        if addr < 0:
            raise InvalidRegisterValueError(f'The value of addr should be greater than 0, not {addr=}.')
    elif isinstance(addr, abc.Iterable) and value is None:
        for _a in addr:
            check_reg_schema(_a, value)
    elif isinstance(addr, abc.Iterable) and isinstance(value, abc.Iterable):
        for _a, _v in zip(addr, value):
            check_reg_schema(_a, _v)
    else:
        raise InvalidRegisterValueError(
            f'Unsupported combination of parameter types value[{type(value)}, {value}], addr[{type(addr)}, {addr}]')
