# 快速开始

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none">返回目录</a>
</div>


<span id="目录"></span>

## 目录
* <a href="#环境安装">环境安装</a>
* <a href="#网络指令">网络指令</a>
* <a href="#串口指令">串口指令</a>
* <a href="#PCI-E指令">PCI-E指令</a>
* <a href="#网络数据流">网络数据流</a>
* <a href="#PCI-E数据流">PCI-E数据流</a>
* <a href="#名词解释">名词解释</a>
* <a href="#工程基本结构">工程基本结构</a>
* [进阶使用](Professional.md)

---

_**NSUKit为一套用于控制设备的快速开发接口。该接口支持向设备发送网络、串口、PCI-E指令，并同时支持网络、PCI-E数据流的上下行。**_
<center>![](introduction_frame_description.png)</center>
<center>NSUKit基本框架</center>

---

<span id="环境安装"></span>

## 环境安装
```shell
python>=3.8

使用虚拟环境进行安装
1. conda create -n NSUKit python=3.9
2. conda activate NSUKit
3. pip install NSUKit

本机环境直接安装
1. pip install NSUKit
```

---
## 使用接口

<span id="网络指令"></span>

### 网络指令
在本工具中，网络指令是指使用TCP/IP通信协议，来实现主机与设备相互通信发送数据的一种方法

<center>![](quick_start_tcp_cmd.png)</center>
设备作为Server端其5001端口常开用于接收指令，本机使用设备IP:5001连接并进行指令收发。

_**网络指令代码示例**_
```python
from nsukit import *
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target="x.x.x.x", port=5001)
nsukit.write(0x1, b'\x02\x00\x00\x00')
nsukit.read(0x1)
nsukit.bulk_write({0x1: b'\x02\x00\x00\x00', 0x2: b'\x03\x00\x00\x00'})
nsukit.bulk_read([0x1, 0x2])
```

<span id="串口指令"></span>

### 串口指令
在本工具中，串口指令是指使用串口线将主机与设备连接，来实现主机与设备相互通信发送数据的一种方法

<center>![](quick_start_serial_cmd.png)</center>
主机与设备使用串口线互联后，根据串口号连接并进行指令收发。

_**串口指令代码示例**_
```python
from nsukit import *
nsukit = NSUKit(SerialCmdUItf, TCPChnlUItf)
nsukit.start_command(target="COM1", target_baud_rate=9600)
nsukit.write(0x1, b'\x02\x00\x00\x00')
nsukit.read(0x1)
nsukit.bulk_write({0x1: b'\x02\x00\x00\x00', 0x2: b'\x03\x00\x00\x00'})
nsukit.bulk_read([0x1, 0x2])
```

<span id="PCI-E指令"></span>

### PCI-E指令
在本工具中，PCI-E指令是指使用PCI-E总线将主机与设备连接，来实现主机与设备相互通信发送数据的一种方法

<center>![quick_start_PCI-E指令连接示意图](quick_start_PCI-E_cmd.png)</center>
将设备插入主机后，根据设备号（0到本机所有插入的设备数量-1）连接并进行指令收发。

_**PCI-E指令代码示例**_
```python
from nsukit import *
nsukit = NSUKit(PCIECmdUItf, PCIEChnlUItf)
nsukit.start_command(target=0, sent_base=0x10000000, recv_base=0x13000000, irq_base=0x00003000 + 44, sent_down_base=0x00003030)
nsukit.write(0x1, b'\x02\x00\x00\x00')
nsukit.read(0x1)
nsukit.bulk_write({0x1: b'\x02\x00\x00\x00', 0x2: b'\x03\x00\x00\x00'})
nsukit.bulk_read([0x1, 0x2])
```

<span id="网络数据流"></span>

### 网络数据流
在本工具中，网络数据流是指使用TCP/IP通信协议，来实现主机与设备相互发送流式数据的一种方法

<center>![quick_start_网络数据流连接示意图](quick_start_tcp_data.png)</center>

_**端口号会根据设备的IP进行自动计算，用户自己指定端口**_

本机作为Server开放端口后，设备自动连接并进行数据传输。

_**网络数据流代码示例**_
```python
from nsukit import *
import threading
event = threading.Event()
length = 1024
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_stream(target="x.x.x.x")
fd = nsukit.alloc_buffer(length)
nsukit.stream_recv(99, fd, length, 0, event.is_set)
print(nsukit.get_buffer(fd, length))
```

<span id="PCI-E数据流"></span>

### PCI-E数据流
在本开发工具中，PCI-E数据流是指使用PCI-E总线将主机与设备连接，来实现主机与设备相互发送流式数据的一种方法

<center>![quick_start_PCI-E数据流连接示意图](quick_start_PCI-E_cmd.png)</center>
将设备插入主机后，根据设备号（0到本机所有插入的设备数量-1）连接并取出数据。

_**PCI-E数据流代码示例**_
```python
from nsukit import *
import threading
event = threading.Event()
length = 1024
nsukit = NSUKit(PCIECmdUItf, PCIEChnlUItf)
nsukit.start_stream(target=0)
fd = nsukit.alloc_buffer(length)
nsukit.stream_recv(0, fd, length, 0, event.is_set)
print(nsukit.get_buffer(fd, length))
```

---

<span id="名词解释"></span>

##  名词解释

_targrt_ : 目标设备的地址。TCP/IP通信协议中为IP地址，PCI-E中为本机中的设备数量减1，串口为设备串口号

_NSUKit_ : 统一调用工具类

_TCPCmdUItf_ : 网络指令类

_SerialCmdUItf_ : 串口指令类

_PCIECmdUItf_ : PCI-E指令类

_TCPChnlUItf_ : 网络数据流类

_PCIEChnlUItf_ : PCI-E数据流类

---

<span id="工程基本结构"></span>

## 工程基本结构
本快速开发工具基本结构如下所示，下图展示了NSUKit中的所有可调用功能

![quick_start_工程基本结构](quick_start_basic.png)
<center>用户直接调用NSUKit类，使用NSUKit的功能</center>

---

<center>Copyright © 2023 理工数字系统实验室 <a href="http://naishu.tech/" target="_blank">naishu.tech</a></center>
<center>北京耐数电子有限公司</center>
    