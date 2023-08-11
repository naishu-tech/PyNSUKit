# 快速开始
### 环境安装
    - conda create -n NSUKit python=3.9
    - conda activate NSUKit
    - pip install NSUKit
### 使用接口
``` python
from nsukit import *

# 使用TCP指令+TCP数据流
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
nsukit.start_stream(target="127.0.0.1", port=6001)

# 使用Serial指令+TCP数据流
nsukit = NSUKit(SerialCmdUItf, TCPChnlUItf)
nsukit.start_command("COM1", target_baud_rate=9600)
nsukit.start_stream(target="127.0.0.1", port=6001)

# 使用PCIE指令+TCP数据流
nsukit = NSUKit(PCIECmdUItf, TCPChnlUItf)
nsukit.start_command(target=0, sent_base=0, recv_base=0)
nsukit.start_stream(target="127.0.0.1", port=6001)

# 使用TCP指令+PCIE数据流
nsukit = NSUKit(TCPCmdUItf, PCIEChnlUItf)
nsukit.start_stream(target=0)

# 使用Serial指令+PCIE数据流
nsukit = NSUKit(SerialCmdUItf, PCIEChnlUItf)
nsukit.start_stream(target=0)

# 使用PCIE指令+PCIE数据流
nsukit = NSUKit(PCIECmdUItf, PCIEChnlUItf)
nsukit.start_stream(target=0)

# 示例
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)
print(nsukit.read("ADC NCO频率"))
print(nsukit.read(0x1))
print(nsukit.bulk_read([0x1, 0x1]))
print(nsukit.bulk_read([0x1, "ADC NCO频率"]))
print(nsukit.write(0x1, 0x1))
print(nsukit.write("ADC NCO频率", 1))
print(nsukit.bulk_write({0x1: 0x1, 0x2: 0x1}))
print(nsukit.bulk_write({0x1: 0x1, "ADC NCO频率": 1}))
```

### 如何使用
### 名词解释
### 看完就能用起来这套工具

    