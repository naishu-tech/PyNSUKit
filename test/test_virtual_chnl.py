# Copyright (c) [2023] [Mulan PSL v2]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

import pytest

from nsukit.base_kit import KitMeta
from nsukit.interface.base import BaseChnlUItf
from nsukit.middleware.virtual_chnl import VirtualChnlMw


def test_dispenser():
    print('/n')
    class Kit(metaclass=KitMeta):
        ...

    kit = Kit()
    kit.itf_chnl = BaseChnlUItf()
    v_chnl = VirtualChnlMw(kit)
    v_chnl.config(stream_mode='real')
    msg = pytest.raises(NotImplementedError, v_chnl.alloc_buffer, 1024)
    print(msg)

    v_chnl.config(stream_mode='virtual')
    msg = pytest.raises(RuntimeError, v_chnl.stream_send, 0, 1, 1024)
    print(msg)
