# 快速开始
### 环境安装
    ----------------创建虚拟环境----------------
    - conda create -n NSUKit python=3.9
    - conda activate NSUKit
    ----------------安装python依赖-------------
    - pip install NSUKit
### 使用接口
``` python
from nsukit.core.NSUKit import NSUKit
from nsukit.core.interface import CommandTCP, CommandPCIE, CommandSerial, DataTCP

# 使用TCP指令
nsukit = NSUKit(CommandTCP, DataTCP)
nsukit.start_command('127.0.0.1')

# 使用Serial指令
nsukit = NSUKit(CommandSerial, DataTCP)
nsukit.start_command('COM0')

# 使用PCIE指令
nsukit = NSUKit(CommandPCIE, DataTCP)
nsukit.start_command(0)

# 示例
nsukit = NSUKit(CommandTCP, DataTCP)
nsukit.start_command('127.0.0.1')
print(nsukit.read('dds0中心频率'))
print(nsukit.read(0x01))
print(nsukit.bulk_read(['dds0中心频率', 0x01, 'dds0中心频率']))
print(nsukit.write(0x01, 0x04))
print(nsukit.write("dds0中心频率", 0x04))
print(nsukit.bulk_write({0x02: 0x02, "dds0中心频率": 0x04, 0x03: 0x03}))
```

    