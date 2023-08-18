# 进阶使用

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none">返回目录</a>
</div>

<span id="目录"/>

## 目录
* <a href="#工程详细结构结构">工程详细结构结构</a>
* <a href="#NSUKit">NSUKit</a>
* <a href="#TCPCmdUItf">TCPCmdUItf</a>
* <a href="#SerialCmdUItf">SerialCmdUItf</a>
* <a href="#PCIECmdUItf">PCIECmdUItf</a>
* <a href="#TCPChnlUItf">TCPChnlUItf</a>
* <a href="#PCIEChnlUItf">PCIEChnlUItf</a>
* <a href="#icd_paresr">icd_paresr</a>
* <a href="#virtual_chnl">virtual_chnl</a>
* <a href="#自定义接口">自定义接口</a>
* <a href="#名词解释">名词解释</a>
* [快速开始](Quickstart.md)

---

<span id="工程详细结构结构" />

## 工程详细结构结构
详细的类图

---

<span id="NSUKit" />

## NSUKit
_**NSUKit：统一调用工具类**_

### NSUKit():
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
```python
# 结束发送指令操作。调用该函数，会断开连接（断开TCP、串口、PCI-E连接）
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.stop_command()
```

### write(self, addr, value, execute=True) -> "list | int":
```python
# 修改寄存器地址操作。调用该函数传入寄存器地址和要修改的值，来完成寄存器值修改。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.write(0x1, 0x2)
# 上述改操作意思为：
# ！！注意！！ PCI-E指令会直接将设备地址0x1的值改为0x2
# ！！注意！！ 在网络指令与串口指令中将会发送 (0x5F5F5F5F, 0x31001000, 0x00000000, 24, addr, value) 的二进制数据
# 参数 execute 会在icd_paresr中进行统一讲解
```

### read(self, addr) -> int:
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
```python
# 批量修改寄存器地址操作。调用该函数传入字典，来完成寄存器值批量修改。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.bulk_write({0x1:0x2, 0x3:0x4})
# 批量修改时会根据参数依次调用nsukit.write()函数
```

### bulk_read(self, addrs: list) -> list:
```python
# 批量读取寄存器操作。调用该函数传入要读取寄存器地址，来完成读取操作。
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
print(nsukit.bulk_read([0x1,0x2,0x3]))
# 批量读取时会根据参数依次调用nsukit.read()函数
```

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

### recv_open(self, chnl, fd, length, offset=0):

### wait_dma(self, fd, timeout: int = 0):

### break_dma(self, fd):

### stream_recv(self, chnl, fd, length, offset=0, stop_event=None, flag=1):

### stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):

---

<span id="TCPCmdUItf" />

## TCPCmdUItf
_**TCPCmdUItf：网络指令类**_

---

<span id="SerialCmdUItf" />

## SerialCmdUItf
_**SerialCmdUItf：串口指令类**_

---

<span id="PCIECmdUItf" />

## PCIECmdUItf
_**PCIECmdUItf：PCI-E指令类**_

---

<span id="TCPChnlUItf" />

## TCPChnlUItf
_**TCPChnlUItf：网络数据流类**_

---

<span id="PCIEChnlUItf" />

## PCIEChnlUItf
_**PCIEChnlUItf：PCI-E数据流类**_


---

<span id="icd_paresr" />

## icd_paresr
_**icd_paresr：指令处理中间件**_


---

<span id="virtual_chnl" />

## virtual_chnl
_**virtual_chnl：虚拟通道中间件**_

---

<span id="自定义接口" />

## 自定义接口


---

<span id="名词解释" />

## 名词解释

---


<center>Copyright © 2023 理工数字系统实验室 <a href="http://naishu.tech/" target="_blank">naishu.tech</a></center>
<center>北京耐数电子有限公司</center>