# 🚀快速开始

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none">返回目录</a>
</div>


<span id="目录"></span>

## 目录
1. <a href="#环境安装">环境安装</a>
2. <a href="#指定协议接口">指定协议接口</a>
3. <a href="#发起连接">发起连接</a>
4. <a href="#寄存器交互">寄存器交互</a>
5. <a href="#数据流交互">数据流交互</a>
6. [进阶使用](03_Professional.md)

---

<span id="环境安装"></span>

## 环境安装

### 环境依赖
```text
python = ">=3.8,<4.0"
numpy = ">=1.24"
pyserial = "^3.5"
pandas = "^2.0.3"
```

### 安装
```shell
使用虚拟环境进行安装
1. conda create -n NSUKit python=3.9
2. conda activate NSUKit
3. pip install NSUKit

本机环境直接安装
1. pip install NSUKit
```

---
## 使用接口

<center>![](Interactive_Classification.png)</center>

与板卡常用的基本交互方式可抽象为寄存器交互(cmd)、指令交互(cmd)与数据流交互(stream)三种，不同的板卡会选用不同的物理接口和协议来承载这三种基本交互。

在这三种交互之上，用户可实现基于板卡的不同功能，NSUKit基于这一模型，提出了如下独立于具体板卡的抽象交互接口。

<span id="指定协议接口"></span>

### 指定协议接口
1. 三种交互方式都被划归到了NSUKit类中，只需要在实例化此类时，将对应的CmdItf、StreamItf协议类作为参数传入，再通过InitParamSet数据类指定协议类连接板卡所需的参数
2. NSUKit初始化详情可查看文档[NSUKit.__init__](@ref NSUKit_init)
    ```python
    from nsukit import NSUKit, InitParamSet
    from nsukit.interface import TCPCmdUItf, PCIEStreamUItf
    
    cmd_param = InitParamSet(ip='127.0.0.1')
    stream_param = InitParamSet(board=0)
    
    kit = NSUKit(
        cmd_itf_class=    TCPCmdUItf,
        stream_itf_class= PCIEStreamUItf,
        cmd_param=        cmd_param,
        stream_param=     stream_param
        )
    ```
3. 这样就完成了对应某一具体形态板卡的软件对象实例化，对于三种抽象交互方式的各个接口调用，都不会再出现与具体物理协议相关的参数

<span id="发起连接"></span>

### 发起连接
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

### 寄存器交互

1. <center>![](RegisterInteractionInterface.png)</center>
2. 寄存器交互指以(地址, 值)的形式与板卡进行交互，提供单地址值写入/读取接口，片写入/读取接口
3. [单地址写入](@ref NSUKit_write)/[单地址读出](@ref NSUKit_read)接口以32bit为一个独立寄存器，[片写入](@ref NSUKit_bulk_write)/[片读取](@ref NSUKit_bulk_read)支持任意值长度
   ```python
    from nsukit import NSUKit
    
    ...
    kit: NSUKit
    kit.write(addr=0x10000021, value=b'\x00\x00\x00\x00')
    value: bytes = kit.read(addr=0x00000031)
    kit.bulk_write(base=0x10000030, value=b'\x01\x02\x03\x04'*10, mode='loop')   # 从给定寄存器地址，将给定数据依次写入，地址不递增
    value: bytes = kit.bulk_read(base=0x00000020, length=10, mode='inc')        # 从给定基地址开始，从寄存器中读取指定长度的值
   ```

<span id="指令交互"></span>

### 指令交互
1. <center>![](CommandInteraction.png)</center>
2. 指令交互指以固定的包格式将一系列需要协同配置的参数组织为一条指令下发给板卡，板卡在接收到指令并执行完成后，以约定的包格式进行回执
3. 提供三个指令交互接口，[NSUKit.set_param](@ref NSUKit_set_param)、[NSUKit.get_param](@ref NSUKit_get_param)、[NSUKit.execute](@ref NSUKit_execute)，如下示例使用指令交互接口将板卡的DAC采样率配置为8Gsps
   ```python
    from nsukit import NSUKit
    
    ...
    kit: NSUKit
    kit.set_param(name='DAC采样率', value=8e9)   # 配置指令参数
    kit.execute(cmd='RF配置')                   # 下发配置指令
   ```

<span id="数据流交互"></span>

### 数据流交互
1. <center>![](StreamInterface.png)</center>
2. 数据流交互指板卡与主机间以流的方式进行数据传输，只用指定一个基地址，就可以将一片数据连续不断地从一端传输到另一端，常用于大批量、长时间、高带宽的数据传输场景，详细使用方式可参看[进阶使用](03_Professional.md)
3. 数据流交互接口分为内存管理与数据收发两部分，内存管理([NSUKit.alloc_buffer](@ref NSUKit_alloc_buffer)、[NSUKit.free_buffer](@ref NSUKit_free_buffer)、[NSUKit.get_buffer](@ref NSUKit_get_buffer))用于管理用于数据流交互的host端连续内存。如下示例展示用数据流交互接口阻塞式将16kB数据从板卡传输到主机内存
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
    