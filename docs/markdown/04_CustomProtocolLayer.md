# 自定义协议层


<span id="自定义接口"></span>

## 自定义接口
_**此节描述如何自定义指令、数据流接口，icd、通道中间件**_

### 自定义指令接口
_**自定义指令接口需要重写以下方法**_
```python
import nsukit.interface.base as base

class xxCmdUItf(base.BaseCmdUItf):
    def __init__(self):
        #初始化
        ...

    def accept(self, target: str, **kwargs):
        # 建立指令链接
        ...

    def recv_bytes(self, size: int) -> bytes:
        # 接收数据返回接收的数据（bytes）
        ...

    def send_bytes(self, data: bytes) -> int:
        # 发送数据返回已发送的长度（int）
        ...

    def write(self, addr: int, value: bytes) -> bytes:
        # 寄存器写入返回返回数据（bytes）
        ...

    def read(self, addr: int) -> bytes:
        # 寄存器读取返回读取到的数据（bytes）
        ...

    def close(self):
        # 关闭连接
        ...

    def set_timeout(self, s: int = 5):
        # 设置连接超时时间
        ...
```

### 自定义数据流接口
_**自定义数据流接口需要重写以下方法**_
```python
import nsukit.interface.base as base
import numpy as np
from typing import Union

class xxChnlUItf(base.BaseChnlUItf):
    def __init__(self):
        # 初始化
        ...

    def accept(self, target: str, **kwargs):
        # 建立链接前准备
        ...

    def set_timeout(self, s: int = 5):
        # 设置连接超时时间
        ...

    def open_board(self):
        # 连接设备
        ...

    def close_board(self):
        # 关闭链接
        ...
    
    def alloc_buffer(self, length: int, buf: Union[int, np.ndarray, None] = None) -> int:
        # 开辟一块缓存返回缓存地址号
        ...
    
    def free_buffer(self, fd):
        # 释放一块缓存传入缓存地址号
        ...
    
    def get_buffer(self, fd, length):
        # 获取一块缓存中的数据，传入缓存地址号，要获取多长的数据。返回同等长度的数据
        ...
    
    def send_open(self, chnl, fd, length, offset=0):
        # 开启一次数据流下行
        ...
    
    def recv_open(self, chnl, fd, length, offset=0):
        # 开启一次数据流上行，返回True/False
        ...

    def wait_dma(self, fd, timeout: int = 0):
        # 等待完成一次dma操作，返回当前内存中的数据大小
        ...

    def break_dma(self, fd):
        # 结束当前的dma操作，返回当前内存中的数据大小
        ...

    def stream_recv(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        # 将完整的数据流上行封装好，返回True/False
        ...

    def stream_send(self, chnl, fd, length, offset=0, stop_event=None, time_out=5, flag=1):
        # 将完整的数据流下行封装好
        ...
```