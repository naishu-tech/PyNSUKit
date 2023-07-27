import time

from nsukit.core.NSUKit import NSUKit
from nsukit.core.interface import CommandTCP, CommandPCIE, CommandSerial, DataTCP


# 网络指令
def test_cmd_tcp1():
    # TCP写指令测试
    nsukit = NSUKit(CommandTCP, DataTCP)
    nsukit.start_command('127.0.0.1')
    print(nsukit.write('dds0中心频率'))
    print(nsukit.write(0x01))
    print(nsukit.bulk_write({0x02: 0x02, "dds0中心频率": 0x04, 0x03: 0x03}))
    time.sleep(2)


def test_cmd_tcp2():
    # TCP读指令测试
    nsukit = NSUKit(CommandTCP, DataTCP)
    nsukit.start_command('127.0.0.1')
    print(nsukit.read('dds0中心频率'))
    print(nsukit.read(0x01))
    print(nsukit.bulk_read(['dds0中心频率', 0x01, 'dds0中心频率']))
    time.sleep(2)


# 串口指令
def test_cmd_serial1():
    # 串口写指令测试
    nsukit = NSUKit(CommandSerial, DataTCP)
    nsukit.start_command("COM1")
    print(nsukit.write(0x01, 0x04))
    print(nsukit.write("dds0中心频率", 0x04))
    print(nsukit.bulk_write({0x02: 0x02, "dds0中心频率": 0x04, 0x03: 0x03}))
    nsukit.stop_command()
    time.sleep(2)


def test_cmd_serial2():
    # 串口读指令测试
    nsukit = NSUKit(CommandSerial, DataTCP)
    nsukit.start_command("COM1")
    print(nsukit.read('dds0中心频率'))
    print(nsukit.read(0x01))
    print(nsukit.bulk_read(['dds0中心频率', 0x01, 'dds0中心频率']))
    nsukit.stop_command()
    time.sleep(2)


# PCIE指令
def test_cmd_PCIE1():
    # PCIE写指令测试
    nsukit = NSUKit(CommandPCIE, DataTCP)
    nsukit.start_command(0)
    print(nsukit.write(0x01, 0x04))
    print(nsukit.write("dds0中心频率", 0x04))
    print(nsukit.bulk_write({0x02: 0x02, "dds0中心频率": 0x04, 0x03: 0x03}))
    time.sleep(2)


def test_cmd_PCIE2():
    # PCIE读指令测试
    nsukit = NSUKit(CommandPCIE, DataTCP)
    nsukit.start_command(0)
    print(nsukit.read('dds0中心频率'))
    print(nsukit.read(0x01))
    print(nsukit.bulk_read(['dds0中心频率', 0x01, 'dds0中心频率']))
    time.sleep(2)


def test_data_TCP():
    nsukit = NSUKit(CommandTCP, DataTCP)
    nsukit.start_stream('127.0.0.1')
    print(nsukit.read_stream(48))
