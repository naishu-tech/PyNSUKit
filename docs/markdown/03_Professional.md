# 进阶使用

<div style="position: fixed; top: 90%; left: 90%">
<a href="#目录" style="text-decoration: none">返回目录</a>
</div>

<span id="目录"></span>

## 目录
* <a href="#基本结构">基本结构</a>
* <a href="#自闭环仿真">自闭环仿真</a>
* <a href="#数据流交互">数据流交互</a>
* [自定义协议层](04_CustomProtocolLayer.md)
* [自定义处理层](05_CustomProcessingLayer.md)

---
<span id="基本结构"></span>

## 基本结构

<center>![](introduction_global.png)</center>

1. 本SDK提供的接口主要针对射频/数字组件与cpu的交互，将整个交互流程划分为`请求层`、`处理层`、`协议层`三个部分
   1. **请求层**:
      1. 将组件提供的各种参数的读取和配置，看作对一个寄存器的读写，那么参数名即为`寄存器地址`，参数值为`寄存器值`
      2. 将与组件的数据流交互看作一次次DMA，可以指定使用的dma通道、内存地址、数据大小等进行一次dma
   2. **处理层**: 组件与cpu之间可能会约定各种各样的上层交互协议，那么可以在中间处理这一部分中实现上层协议，并将此协议的最终控制接口转为请求所需的读写寄存器和DMA格式
   3. **协议层**: 对诸如TCP、串口、axi_lite、axi_stream等标准通信协议，进行封装。
2. 基于这三个部分的划分，`协议层`、`处理层`的变更不会影响基于`请求层`开发的任何程序

---

<span id="自闭环仿真"></span>

## 自闭环仿真

1. 提供SimCmdUItf、SimStreamUItf两个虚拟协议类，可以模拟与板卡的通信过程，支持写入记忆、数据流仿真等一系列功能，方便 **在没有硬件条件时测试上层程序** 
2. 
   ```python
   from nsukit import NSUKit
   from nsukit.interface import SimCmdUItf, SimStreamUItf
   
   kit = NSUKit(SimCmdUItf, SimChnlUItf)
   kit.link_cmd()
   kit.link_stream()
   kit.write(0x10, b'\x01\x02\x03\x04')
   ...
   ```

---

<span id="数据流交互"></span>

## 数据流交互

### 同步方式
<center>![](block_stream_show.png)</center>

1. 同步方式数据流交互接口: [NSUKit.stream_send](@ref NSUKit_stream_send)、[NSUKit.stream_recv](@ref NSUKit_stream_recv)
2. 如下示例在host上申请了一片1G的内存，对前1kB写入数据20，将这1kB数据下发到板卡

```python
from nsukit import NSUKit

...
kit: NSUKit
fd = kit.alloc_buffer(length=1024**3)
buf = kit.get_buffer(fd, 1024**3)
buf[:1024] = 20
kit.stream_send(chnl=0, fd=fd, length=1024, offset=0)
```

### 异步方式
<center>![](async_stream_itf.png)</center>

1. 提供异步数据流交互接口: [NSUKit.open_send](@ref NSUKit_open_send)、[NSUKit.open_recv](@ref NSUKit_open_recv)、[NSUKit.wait_stream](@ref NSUKit_wait_stream)、[NSUKit.break_stream](@ref NSUKit_break_stream)
2. 接口在开启数据流后立即返回，不等待说有数据传输完成，用户可以在数据流传输过程中继续执行其它操作

```python
from nsukit import NSUKit

...
kit: NSUKit
fd = kit.alloc_buffer(length=1024**3)
res = kit.open_send(chnl=0, fd=fd, length=1024**3, offset=0)
kit.execute('状态查询')
print(kit.get_param('板卡温度'))
if res != -1:
   while res != 1024**3:
      res = kit.wait_stream(fd, timeout=0.05)
```

---


<center>Copyright © 2023 耐数 <a href="http://naishu.tech/" target="_blank">naishu.tech</a></center>
<center>北京耐数电子有限公司</center>