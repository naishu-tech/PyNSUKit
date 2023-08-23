# 进阶使用

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none">返回目录</a>
</div>

<span id="目录"></span>

## 目录
* <a href="#NSUKit">NSUKit</a>
* <a href="#icd_paresr">icd_paresr</a>
* <a href="#virtual_chnl">virtual_chnl</a>
* <a href="#自定义接口">自定义接口</a>
* <a href="#工程详细结构结构">工程详细结构结构</a>
* <a href="#TCPCmdUItf">TCPCmdUItf</a>
* <a href="#SerialCmdUItf">SerialCmdUItf</a>
* <a href="#PCIECmdUItf">PCIECmdUItf</a>
* <a href="#TCPChnlUItf">TCPChnlUItf</a>
* <a href="#PCIEChnlUItf">PCIEChnlUItf</a>
* <a href="#名词解释">名词解释</a>
* [快速开始](Quickstart.md)

---

<span id="NSUKit"></span>

## NSUKit
_**NSUKit：统一调用工具类**_

### NSUKit():

<center>![](professional_NSUKit_NSUKit.png)</center>
<center>NSUKit初始化</center>

```python
# 统一调用工具类实例化
from nsukit import *
# 初始化时需要传入两个接口类，第一个为指令类，第二个为数据流类
# 指令类与数据流类无绑定关系、需根据实际使用自行传入
# 指令类：TCPCmdUItf、SerialCmdUItf、PCIECmdUItf
# 数据流类：TCPChnlUItf、PCIEChnlUItf
# 也可根据自己需要实现属于自己指令、数据流接口，具体方法见目录中自定义接口
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
```

### start_command(self, target=None, **kwargs) -> None::

<center>![](professional_NSUKit_start_command.png)</center>
<center>与设备建立连接</center>

```python
# 发送指令前准备。调用该函数并传入对应的参数以完成指令类、指令处理中间件的初始化操作。
from nsukit import *

# 网络指令
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)

# 串口指令
nsukit = NSUKit(SerialCmdUItf, TCPChnlUItf)
nsukit.start_command(target="COM1", target_baud_rate=9600)

# PCI-E指令
nsukit = NSUKit(PCIECmdUItf, TCPChnlUItf)
nsukit.start_command(target=0, sent_base=0x10000000, recv_base=0x13000000, irq_base=0x00003000 + 44, sent_down_base=0x00003030)

# 也可将参数封装好，直接传入到函数中
param = {
    'tcp_cmd': {
        "port": 5001,
        "check_recv_head": False
    },
    'serial_cmd': {
        "target_baud_rate": 9600,
        "check_recv_head": False
    },
    'pcie_cmd': {
        "sent_base": 0x10000000,
        "recv_base": 0x13000000,
        "irq_base": 0x00003000 + 44,
        "sent_down_base": 0x00003030,
        "check_recv_head": False
    }
}
nsukit.start_command(target='127.0.0.1',  **param["tcp_cmd"])
nsukit.start_command(target="COM1",  **param["serial_cmd"])
nsukit.start_command(target=0,  **param["pcie_cmd"])
```

### stop_command(self) -> None:

<center>![](professional_NSUKit_stop_command.png)</center>
<center>与设备断开连接</center>

```python
# 结束发送指令操作。调用该函数，会断开连接（断开TCP、串口、PCI-E连接）
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.stop_command()
```

### write(self, addr: int, value: bytes) -> bytes:

<center>![](professional_NSUKit_write.png)</center>
<center>向指定地址写入数据</center>

```python
# 修改寄存器地址操作。调用该函数传入寄存器地址和要修改的值，来完成寄存器值修改。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.write(0x1, b'\x02\x00\x00\x00')
# 上述改操作意思为：
# ！！注意！！ PCI-E指令会直接将设备地址0x1的值改为0x2
# ！！注意！！ 在网络指令与串口指令中将会发送 (0x5F5F5F5F, 0x31001000, 0x00000000, 24, addr, value) 的二进制数据
# 参数 execute 会在icd_paresr中进行统一讲解
```

### read(self, addr: int) -> bytes:

<center>![](professional_NSUKit_read.png)</center>
<center>读取指定地址数据</center>

```python
# 读取寄存器操作。调用该函数传入要读取寄存器地址，来完成读取操作。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
print(nsukit.read(0x1))
# 上述改操作意思为：
# ！！注意！！ PCI-E指令会直接将设备地址0x1的值返回
# ！！注意！！ 在网络指令与串口指令中将会发送 (0x5F5F5F5F, 0x31001001, 0x00000000, 20, addr) 的二进制数据
```

### bulk_write(self, params: dict) -> list:

<center>![](professional_NSUKit_bulk_write.png)</center>
<center>批量向指定地址写入数据</center>

```python
# 批量修改寄存器地址操作。调用该函数传入字典，来完成寄存器值批量修改。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.bulk_write({0x1: b'\x02\x00\x00\x00', 0x2: b'\x03\x00\x00\x00'})
# 批量修改时会根据参数依次调用nsukit.write()函数
```

### bulk_read(self, addrs: list) -> list:

<center>![](professional_NSUKit_bulk_read.png)</center>
<center>批量读取指定地址数据</center>

```python
# 批量读取寄存器操作。调用该函数传入要读取寄存器地址，来完成读取操作。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
print(nsukit.bulk_read([0x1,0x2,0x3]))
# 批量读取时会根据参数依次调用nsukit.read()函数
```

---

_**以下函数为数据流相关函数，只有一张附图**_
<center>![](professional_NSUKit_stream_recv.png)</center>
<center>数据流相关附图</center>

### start_stream(self, target=None, **kwargs):

```python
# 开启数据流前的操作。调用该函数根据目标设备类型传入参数、参数建立链接
from nsukit import *
# 网络数据流
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target='127.0.0.1')
# or
nsukit.start_stream(target='127.0.0.1', port=6001)

# PCI-E数据流
nsukit = NSUKit(TCPCmdUItf, PCIEChnlUItf)
nsukit.start_stream(target=0)
# 根据传入参数与设备建立数据流连接
# ！！注意！！ 网络数据流在不传入端口号时会根据设备ip自动计算端口号，如传入端口号会使用传入的端口号
```

### stop_stream(self):
```python
# 接收完数据后操作。调用该函数关闭数据流链接
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target='127.0.0.1')
nsukit.stop_stream()
# 断开当前数据流链接
```

### alloc_buffer(self, length, buf: int = None):
```python
# 开辟一块缓存。调用该函数申请一块内存，用于存储设备测试数据
from nsukit import *
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
# or
fd = nsukit.alloc_buffer(length, fd)
# 根据传入的长度申请一块内存
# ！！注意！！ 这里的1长度 = 4 bytes，上述程序length中大小为 1024*4 bytes
# ！！注意！！ 申请的内存不可长久存储，程序退出后将清空已申请的内存
```

### free_buffer(self, fd):
```python
# 释放一块已申请的内存。调用该函数来释放已经用完的缓存，用于释放系统资源
from nsukit import *
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
nsukit.free_buffer(fd)
# 根据传入的内存地址将其释放
```

### get_buffer(self, fd, length):
```python
# 获取内存中存储的数据。调用该函数根据参数来获取指定内存中指定长度的数据
from nsukit import *
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
print(nsukit.get_buffer(fd, 1024))
# 获取内存中的数据
# ！！注意！！ 这里的1长度 = 4 bytes，上述程序length中大小为 1024*4 bytes
```

### send_open(self, chnl, fd, length, offset=0):
```python
# 暂不支持
# ！！注意！！ 数据上下行是以设备角度进行描述的，设备的数据上行，设备的数据下行
```

### recv_open(self, chnl, fd, length, offset=0):
```python
# 开启数据上行。调用该函数根据参数开启数据上行
from nsukit import *
# 网络数据流上行
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
nsukit.recv_open(chnl=9999, fd=fd, length=1024, offset=0)

# PCI-E数据流上行
nsukit = NSUKit(TCPCmdUItf, PCIECmdUItf)
nsukit.start_stream(target=0)
fd = nsukit.alloc_buffer(length)
nsukit.recv_open(chnl=0, fd=fd, length=1024, offset=0)
# 开启数据流上行
# ！！注意！！ 数据上下行是以设备角度进行描述的，设备的数据上行，设备的数据下行
# ！！注意！！ 因网络数据流没有通道的概念故chnl参数填写任意数字即可，PCIE数据流有通道概念故根据实际情况填写通道编号
```

### wait_dma(self, fd, timeout: int = 0):
```python
# 等待完成一次dma操作。调用该函数传入对应的内存地址来查看内存已经使用的大小
from nsukit import *
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
nsukit.recv_open(chnl=9999, fd=fd, length=1024, offset=0)
print(nsukit.wait_dma(fd=fd, timeout=5))
# 等待完成一次dma操作
# !!注意！！ wait_dma()可能不会立即完成
```

### break_dma(self, fd):
```python
# 终止本次dma操作。调用该函数传入对应的内存地址来停止本次dma操作，并返回内存已经使用的大小
from nsukit import *
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
nsukit.recv_open(chnl=9999, fd=fd, length=1024, offset=0)
print(nsukit.break_dma(fd=fd))
# 终止本次dma操作
# !!注意！！ nsukit.break_dma()可能不会立即完成
```

### stream_recv(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
```python
# 预封装好的数据流上行函数。调用预封装好的数据流上行函数可快速开始使用本工具
from nsukit import *
import threading
length = 1024
event = threading.Event()
# 网络数据流
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="192.168.1.179")
fd = nsukit.alloc_buffer(length)
nsukit.stream_recv(99, fd, length, 0, event.is_set)

# PCI-E数据流
nsukit = NSUKit(TCPCmdUItf, PCIEChnlUItf)
fd = nsukit.alloc_buffer(length)
nsukit.start_stream(target=0)
nsukit.stream_recv(0, fd, length, 0, event.is_set)

# 预封装好的数据流上行。函数内部分别调用了recv_open,wait_dma
# ！！注意！！ 该函数会阻塞
# ！！注意！！ 符合规则的数据流上行开启方法应该是：
# ！！注意！！ NSUKit(初始化) -> nsukit.start_stream(建立数据流链接) -> nsukit.alloc_buffer(开辟缓存) -> nsukit.stream_recv(开始上行) -> nsukit.stop_stream(关闭链接)
```

### stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):
```python
# 暂不支持
```

---

<span id="icd_paresr"></span>

## icd_paresr
_**icd_paresr：指令处理中间件，用来使用约定式的icd指令**_

<center>![](professional_icd_parser.png)</center>
<center>icd_parser结构</center>

```python
# 该类不用单独调用及初始化
# 在NSUKit的nsukit.start_command()中会自动调用config()进行初始化，并使用nsukit文件夹下的icd.json
# icd.json可根据实际情况按照规定格式进行更改

```

### icd.json

<center>![](professional_icd_parser_icd.json.png)</center>
<center>icd.json文件格式</center>

```python
# icd.json是指令处理中间件的必要文件
# 其文件格式可以大概描述为
```

```json
{
    "param": {
        "参数1": ["参数1", "数据类型", "数据值"],
        "参数2": ["参数2", "数据类型", "数据值"],
        "参数3": ["参数3", "数据类型", "数据值"]
    },
    "command":{
        "指令1": {
            "send": [
              "参数1", 
              "参数2", 
              ["参数4", "数据类型", "数据值"]
            ],
            "recv": [
              "参数3"
            ]
        },
        "指令2": {
            "send": [
              "参数1",
              "参数2",
              ["参数4", "数据类型", "数据值"]
            ],
            "recv": [
              "参数3"
            ]
        }
    },
    "sequence": {
        "指令3": [
            "参数",
            ["参数", "数据类型", "数据值"]
        ]
    }
}
```

```python
# 暨以上三大类，由param、command、sequence组成
# param中有多个参数
# command中有两种指令类型 send、recv， 每种指令由多个参数拼接而成
# sequence 指令的变长部分，每一项为一list，结构与command中的项相同，其可在command中被调用{{sequence1}}，程序自动根据excel文件中的内容重复一项
# ！！注意！！ 参数中支持以下数据类型uint8、int8、uint16、int16、uint32、int32、float、double、file_data、file_length
```

### config(self, **kwargs): 
```python
# 初始化指令处理中间件。该函数不用单独调用
# 在NSUKit的start_command中会自动调用
# 在调用时可附加参数以使用特定icd.json文件 例如：
from nsukit import *
param = {
    'tcp_cmd': {
        "port": 5001,
        "check_recv_head": False,
        "icd_path": "icd文件路径"
    }
}
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', **param)
# 其中icd_path为使用指定的icd.json路径（绝对路径）
# check_recv_head为是否按照icd文件中指令的recv进行强验证
# check_recv_head开启时：（返回指令）按照recv格式（包头，id，序号，长度，结果），进行强验证 即包头，id，序号必须为recv中所写的数值
# check_recv_head关闭时：（返回指令）按照recv格式直接进行存储
# check_recv_head默认关闭
```

---

<center>![](professional_icd_parser_getset_param.png)</center>
<center>get_param/set_param调用流程</center>

### get_param(self, param_name: str, default=0, fmt_type=int):
```python
# 获取icd中某个参数的的值。该函数不用单独调用
# 在read函数中当add为字符型，且该字符是参数名时自动调用 例如：
from nsukit import *
param = {
    'tcp_cmd': {
        "port": 5001,
        "check_recv_head": False,
        "icd_path": "icd文件路径"
    }
}
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', **param)
nsukit.read("参数1")
```

### set_param(self, param_name: str, value, fmt_type=int):
```python
# 设置icd中某个参数的的值。该函数不用单独调用
# 在write函数中当add为字符型，且该字符是参数名时自动调用 例如：
from nsukit import *
param = {
    'tcp_cmd': {
        "port": 5001,
        "check_recv_head": False,
        "icd_path": "icd文件路径"
    }
}
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', **param)
nsukit.write(addr="参数1", value=1)
#！！注意！！ 在默认情况下write在更改完参数时会自动执行与之相关的指令，如不想直接执行请增加参数execute=False
nsukit.write(addr="参数1", value=1, execute=False)
# 当addr为指令名时会直接发送对应指令，此时value可以填任何数
nsukit.write(addr="指令1", value=123)
```

---

<span id="virtual_chnl"></span>

## virtual_chnl
_**virtual_chnl：虚拟通道中间件**_
```text
虚拟通道主要用于：当设备只有1个数传通道，但想分开传输多路数据时所使用
```

### virtual_chnl未开启时

<center>![](professional_virtual_chnl_stop.png)</center>
<center>虚拟通道未开启时数据流的流程图</center>

```text
举例说明：
花园需要浇水，每种花需要浇不同的水，且每种水不相容。现在只有一个水管（1个数传通道）
当我用水管进行浇水时，我需要一个挡板把水管中的不同的水分开进行使用
```

### virtual_chnl开启时

<center>![](professional_virtual_chnl_start.png)</center>
<center>虚拟通道开启时数据流的流程图</center>

```text
举例说明：(还是上边的例子)
花园需要浇水，每种花需要浇不同的水，且每种水不相容。现在只有一个水管（1个数传通道）
现在我买了一台机器，这台机器上有很多出水口，并且机器可以自动把每种水自动分开
这时我只需要使用机器上对应出水口的水去浇特定的花就可以了
```

---

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

---

<span id="工程详细结构结构"></span>

## 工程详细结构结构

<center>![](professional_detail.png)</center>

---

<span id="TCPCmdUItf"></span>

## TCPCmdUItf
_**TCPCmdUItf：网络指令类**_

<center>![](professional_tcp_cmd.png)</center>

---

<span id="SerialCmdUItf"></span>

## SerialCmdUItf
_**SerialCmdUItf：串口指令类**_

<center>![](professional_serial_cmd.png)</center>

---

<span id="PCIECmdUItf"></span>

## PCIECmdUItf
_**PCIECmdUItf：PCI-E指令类**_

<center>![](professional_PCI-E_cmd.png)</center>

---

<span id="TCPChnlUItf"></span>

## TCPChnlUItf
_**TCPChnlUItf：网络数据流类**_

<center>![](professional_tcp_data.png)</center>

---

<span id="PCIEChnlUItf"></span>

## PCIEChnlUItf
_**PCIEChnlUItf：PCI-E数据流类**_

<center>![](professional_PCI-E_data.png)</center>

---

<span id="名词解释"></span>

## 名词解释

_数据流上行_ : 以设备的角度描述数据流的收发，数据流上行是指设备将数据发送给本机

_数据流下行_ : 以设备的角度描述数据流的收发，数据流下行是指本机将数据发送给设备

---


<center>Copyright © 2023 理工数字系统实验室 <a href="http://naishu.tech/" target="_blank">naishu.tech</a></center>
<center>北京耐数电子有限公司</center>