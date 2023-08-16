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
