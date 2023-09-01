# 变更记录

## Unreleased

## v0.1.2 (2023-09-01)

### Feat

- **0.1.2**: 重新定义了一系列对外接口和相关概念

## v0.1.1 (2023-08-24)

## V0.1.0 (2023-08-23)

### Feat

- **完善文档**: 继续进行文档完善
- **文档**: 增加更新记录页面，完善快速开始和进阶使用
- **文档**: 编写快速开始、进阶使用文档
- **VirtualChnlMw**: 完成虚拟通道中间件
- **添加接口**: 添加接口param_is_command。
- **注释**: 注释核对
- **注释**: base_kit注释 icd_parser注释
- **注释**: interface注释，pytest注释
- **接口**: 外部接口优化,icd指令流程完善
- **tcp数据流**: TCP数据流初步封装
- **项目结构**: 项目整体结构调整，引入python环境/工程管理工具poetry，暂未加入发布相关内容
- **NSUKit**: TCP数据流开发
- **NSUKit**: TCP数据流

### Fix

- **修改图片名称**: 更改所有图片名称为英文，放入image文件夹，doxygen导入图片不能识别中文
- **更改目录结构**: 将文档相关单独建立文件夹进行存储
- **read、write**: write的value直接传bytes，返回值为bytes。read的返回值改为bytes
- **接口名称**: 接口名称修改stream_read->stream_recv，find_command->execute_icd_command。
- **icd**: icd.json文件完善。
- **icd_parser**: 发送icd指令时选择是否强验证包头。
- **interface**: pcie下发指令可选wait_irq和轮询去等待,tcp更改发指令和接收数据流逻辑。
- **xdma**: fpga_recv_open = 0。
- **注释、指令带文件**: 注释核对，增加部分注释，支持带文件指令，icd文件格式更新
- **包头解析**: 修改包头的解析错误，更改部分注释和重写pytest
