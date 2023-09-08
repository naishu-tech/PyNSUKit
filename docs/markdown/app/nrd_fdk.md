# NRD FDK

@todo 描述NRD FDK的适用范围、基本架构，交互接口，提供ICD列表、寄存器列表，说明数据打包格式、波形装载方式

_如果您是第一次使用NRD FDK开发套件或未接触过主机与板卡指令交互的相关方式，可以先阅读 [ICD文件格式](#md_ICD文件格式)_

## 1. 指令交互

### 1.1. ICD列表

### 1.2. 指令交互示例

关于NSUKit的详细介绍可参照：nsukit的 [快速开始](../02_Quickstart.md)

```python
from nsukit import NSUKit

...
kit: NSUKit
kit.set_param(name='DAC采样率', value=8e9)   # 配置指令参数
value = kit.get_param(name='DAC采样率')   # 获取参数名为
kit.execute(cmd='RF配置')
```

---
## 2. 寄存器交互

### 2.1. 寄存器列表

### 2.2. 指令交互示例

关于NSUKit的详细介绍可参照：nsukit的 [快速开始](../02_Quickstart.md)

```python
from nsukit import NSUKit
    
...
kit: NSUKit
kit.write(addr=0x10000021, value=b'\x00\x00\x00\x00')
value: bytes = kit.read(addr=0x00000031)
```

---
## 3. 数据流交互

。。。

---

<center>Copyright © 2023 耐数 <a href="http://naishu.tech/" target="_blank">naishu.tech</a></center>
<center>北京耐数电子有限公司</center>