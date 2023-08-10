# 快速开始
### 环境安装
    ----------------创建虚拟环境----------------
    - conda create -n NSUKit python=3.9
    - conda activate NSUKit
    ----------------安装python依赖-------------
    - pip install NSUKit
### 使用接口
``` python
from nsukit import *

# 使用TCP指令
nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
nsukit.start_command(target='127.0.0.1', port=5001)

# 使用Serial指令
nsukit = NSUKit(SerialCmdUItf, TCPChnlUItf)
nsukit.start_command("COM1", target_baud_rate=9600)

# 使用PCIE指令
nsukit = NSUKit(PCIECmdUItf, TCPChnlUItf)
nsukit.start_command(target=0, sent_base=0, recv_base=0)

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

    