# 🚀快速开始

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none">返回目录</a>
</div>


<span id="目录"></span>

## 目录
1. [环境安装](#md_环境安装)
2. [使用接口](#md_使用接口)
   1. <a href="#指定协议接口">指定协议接口</a>
   2. <a href="#发起连接">发起连接</a>
   3. <a href="#寄存器交互">寄存器交互</a>
   4. <a href="#数据流交互">数据流交互</a>

---
## 1. 环境安装        {#md_环境安装}

### 1.1. 环境依赖
```text
python = ">=3.8,<4.0"
numpy = ">=1.24"
pyserial = "^3.5"
pandas = "^2.0.3"
```

### 1.2. 支持的操作系统与平台
```text
Windows7 x64
Windows10 x64
Windows11 x64

Ubuntu 18.04 aarch64
Ubuntu 18.04 x64
Ubuntu 20.04 aarch64
Ubuntu 20.04 x64

CentOS 8.x x64

macOS 功能受限
```

### 1.3. 安装
```shell
使用虚拟环境进行安装
1. conda create -n NSUKit python=3.9
2. conda activate NSUKit
3. pip install NSUKit

本机环境直接安装
1. pip install NSUKit
```

---

## 2. 使用接口             {#md_使用接口}

<center>![](Interactive_Classification.png)</center>

1. 与板卡常用的基本交互方式可抽象为寄存器交互(cmd)、指令交互(cmd)与数据流交互(stream)三种，不同的板卡会选用不同的物理接口和协议来承载这三种基本交互。
2. 指令交互指以固定的包格式将一系列需要协同配置的参数组织为一条指令下发给板卡，板卡在接收到指令并执行完成后，以约定的包格式进行回执。
   1. 主要发生在 **主机** 与 **板上/片上通用处理核** 之间，两者之间轻松建立复杂的通信协议，可以以更为人类友好的方式进行通信
   2. 主机将某一功能相关的参数打包封装成一条指令统一下发给 板上/片上通用处理核，由处理核翻译成内部参数，并按逻辑时序配置给FPGA
3. 寄存器交互指以(地址, 值)的形式与板卡进行交互
   1. 主要发生在 **FPGA等可编程门阵列** 与 **主机** 端，在不存在通用处理核进行中转处理时，主机需要直接控制FPGA上的硬件逻辑进行工作
4. 数据流交互以流的方式进行数据传输，只用指定一个基地址，就可以将一片数据连续不断地从一端传输到另一端
5. 在这三种交互之上，用户可实现基于板卡的不同功能，NSUKit基于这一模型，提出了如下独立于具体板卡的抽象交互接口。

<span id="指定协议接口"></span>

### 2.1. 指定协议接口
1. 采用面向对象的方式，可以对每个板卡都实例化一个此类的对象，对象包含了三种交互方式的所有控制接口
2. 只需要在实例化此类时，将对应的CmdItf、StreamItf协议类作为参数传入，再通过InitParamSet数据类指定协议类连接板卡所需的参数
3. NSUKit初始化详情可查看文档[NSUKit.__init__](#nsukit.base_kit.NSUKit.__init__)
   ```python
    from nsukit import NSUKit, InitParamSet
    from nsukit.interface import TCPCmdUItf, PCIEStreamUItf
    
    param = InitParamSet(
       cmd_ip='127.0.0.1',
       stream_board=0)
    
    kit = NSUKit(
       cmd_itf_class=    TCPCmdUItf,
       stream_itf_class= PCIEStreamUItf,
       link_param=       param)
   ```
4. 这样就完成了对应某一具体形态板卡的软件对象实例化，对于三种抽象交互方式的各个接口调用，都不会再出现与具体物理协议相关的参数

<span id="发起连接"></span>

### 2.2. 发起连接
1. 在此接口被调用时，主机端会按指定的物理协议对板卡发起连接，cmd与stream可分开link，link完成后，相应的交互接口才可用
2. 
   ```python
    from nsukit import NSUKit
    ...
    kit: NSUKit
    kit.link_cmd()      # 初始化指令
    kit.link_stream()   # 初始化数据流
   ```

<span id="寄存器交互"></span>

### 2.3. 寄存器交互

<center>![](RegisterInteractionInterface.png)</center>

寄存器交互指以(地址, 值)的形式与板卡进行交互，提供单地址值写入/读取接口，片写入/读取接口

#### 2.3.1. 单地址写入/读取
**[单地址写入](#nsukit.base_kit.NSUKit.write)/[单地址读取](#nsukit.base_kit.NSUKit.read)** 是指对一个寄存器地址，传输一个小于等于32位的值

```python
from nsukit import NSUKit
    
...
kit: NSUKit
kit.write(addr=0x10000021, value=b'\x00\x00\x00\x00')
value: bytes = kit.read(addr=0x00000031)
```

#### 2.3.2. 片写入/读取
**[片写入](@ref nsukit.base_kit.NSUKit.bulk_write)/[片读取](@ref nsukit.base_kit.NSUKit.bulk_read)** 是指以寄存器交互方式，传输大于单个寄存器位宽的指定长度的数据

```python
from nsukit import NSUKit
    
...
kit: NSUKit
kit.bulk_write(base=0x10000030, value=b'\x01\x02\x03\x04'*10, mode='inc')   # 从给定寄存器地址，依次将给定数据依次写入后续地址
value: bytes = kit.bulk_read(base=0x00000020, length=10, mode='inc')        # 从给定基地址开始，从寄存器中读取指定长度的值
```

#### 2.3.3. 单址片写入/读取
**[单址片写入](@ref nsukit.base_kit.NSUKit.bulk_write)/[单址片读取](@ref nsukit.base_kit.NSUKit.bulk_read)** 是指将一串指定长度的数据，依次写入单个寄存器地址，由对端将数据从单个寄存器地址中解析出来的方式

```python
from nsukit import NSUKit
    
...
kit: NSUKit
kit.bulk_write(base=0x10000030, value=b'\x01\x02\x03\x04'*10, mode='loop')   # 从给定寄存器地址，将给定数据依次写入，地址不递增
value: bytes = kit.bulk_read(base=0x00000020, length=10, mode='loop')        # 从给定寄存器地址，按一定间隔读出寄存器中的值
```

<span id="指令交互"></span>

### 2.4. 指令交互
<center>![](CommandInteraction.png)</center>

1. 指令交互指以固定的包格式将一系列需要协同配置的参数组织为一条指令下发给板卡，板卡在接收到指令并执行完成后，以约定的包格式进行回执 
2. nsukit内原生支持的**指令包格式**及定义方式可查看文档：[ICD格式](04_ICDScheme.md)
3. 提供三个指令交互接口，[NSUKit.set_param](#nsukit.base_kit.NSUKit.set_param)、[NSUKit.get_param](#nsukit.base_kit.NSUKit.get_param)、[NSUKit.execute](#nsukit.base_kit.NSUKit.execute)，如下示例使用指令交互接口将板卡的DAC采样率配置为8Gsps
#### 2.4.1. 配置参数
接口详情可查看文档 #nsukit.base_kit.NSUKit.set_param ，同时name参数的可用值可参考[此描述](#md_ICDScheme_param_group)

```python
from nsukit import NSUKit

...
kit: NSUKit
kit.set_param(name='DAC采样率', value=8e9)   # 配置指令参数
```

#### 2.4.2. 获取参数
接口详情可查看文档 #nsukit.base_kit.NSUKit.get_param ，同时name参数的可用值可参考[此描述](#md_ICDScheme_param_group)

```python
from nsukit import NSUKit

...
kit: NSUKit
value = kit.get_param(name='DAC采样率')   # 获取参数名为
```

#### 2.4.3. 执行指令
接口详情可查看文档 #nsukit.base_kit.NSUKit.execute ，同时cmd参数的可用值可参考[此描述](#md_ICDScheme_cmd_group)

```python
from nsukit import NSUKit

...
kit: NSUKit
kit.execute(cmd='RF配置')
```

<span id="数据流交互"></span>

### 2.5. 数据流交互
<center>![](StreamInterface.png)</center>

1. 数据流交互指板卡与主机间以流的方式进行数据传输，只用指定一个基地址，就可以将一片数据连续不断地从一端传输到另一端，常用于大批量、长时间、高带宽的数据传输场景，详细使用方式可参看[进阶使用](03_Professional.md)
2. 数据流交互接口分为内存管理与数据收发两部分，内存管理([NSUKit.alloc_buffer](#nsukit.base_kit.NSUKit.alloc_buffer)、[NSUKit.free_buffer](#nsukit.base_kit.NSUKit.free_buffer)、[NSUKit.get_buffer](@ref nsukit.base_kit.NSUKit.get_buffer))用于管理用于数据流交互的host端连续内存。如下示例展示用数据流交互接口阻塞式将16kB数据从板卡传输到主机内存

```python
from nsukit import NSUKit

...
kit: NSUKit
fd = kit.alloc_buffer(16384)                             # 申请一片16384Bytes的内存
kit.stream_recv(chnl=0, fd=fd, length=16384, offset=0)   # 通过通道0将指定数据量存储到申请到的fd上
```

---

<center>Copyright © 2023 耐数 <a href="http://naishu.tech/" target="_blank">naishu.tech</a></center>
<center>北京耐数电子有限公司</center>
    