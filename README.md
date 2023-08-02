## NSUKit 对外开发工具包
    __init__(指令类, 数据流类, icd文件路径) 初始化
        nsukit = NSUKit(CommandTCP, DataTCP)
    start_command(target_id) 开启指令发送
        nsukit.start_command('127.0.0.1')
        nsukit.start_command('COM0')
    stop_command()
    write()
    read()
    bulk_write()
    bulk_read()
    start_stream()
    stop_stream()
    read_stream()
    write_stream()
## Interface 指令&数据流接口
    Command: 指令类
	    CommandTCP: TCP指令
	    CommandSerial: 串口指令
        CommandPCIE: PCIE指令
    Data: 数据流类
        DataTCP: TCP数据流
        DataPCIE: PCIE数据流
## Tools
    icd_parser: icd工具