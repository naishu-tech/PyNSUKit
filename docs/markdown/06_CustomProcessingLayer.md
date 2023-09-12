# 自定义处理层

@todo 自定义处理层

<span id="icd_paresr"></span>

## icd_paresr     {#md_icd_paresr}
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
nsukit = NSUSoc(TCPCmdUItf, TCPChnlUItf)
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
nsukit = NSUSoc(TCPCmdUItf, TCPStreamUItf)
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
nsukit = NSUSoc(TCPCmdUItf, TCPStreamUItf)
nsukit.start_command(target='127.0.0.1', **param)
nsukit.write(addr="参数1", value=1)
# ！！注意！！ 在默认情况下write在更改完参数时会自动执行与之相关的指令，如不想直接执行请增加参数execute=False
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

