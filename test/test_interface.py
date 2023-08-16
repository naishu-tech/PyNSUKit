import threading

from nsukit import *


def test_nsukit_cmd_tcp():
    """!
    @brief 网络指令读写测试
    @details read:读, write:写, bulk_read: 批量读, bulk_write:批量写
    @return:
    """
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


def test_nsukit_cmd_pcie():
    """!
    @brief pcie指令读写测试
    @details read:读, write:写, bulk_read: 批量读, bulk_write:批量写
    @return:
    """
    nsukit = NSUKit(PCIECmdUItf, TCPChnlUItf)
    nsukit.start_command(target=0, sent_base=0, recv_base=0)
    print(nsukit.read("ADC NCO频率"))
    print(nsukit.read(0x1))
    print(nsukit.bulk_read([0x1, 0x1]))
    print(nsukit.bulk_read([0x1, "ADC NCO频率"]))
    print(nsukit.write(0x1, 0x1))
    print(nsukit.write("ADC NCO频率", 1))
    print(nsukit.bulk_write({0x1: 0x1, 0x2: 0x1}))
    print(nsukit.bulk_write({0x1: 0x1, "ADC NCO频率": 1}))


def test_nsukit_cmd_serial():
    """!
    @brief 串口指令读写测试
    @details read:读, write:写, bulk_read: 批量读, bulk_write:批量写
    @return:
    """
    nsukit = NSUKit(SerialCmdUItf, TCPChnlUItf)
    nsukit.start_command("COM1", target_baud_rate=9600)
    print(nsukit.read("ADC NCO频率"))
    print(nsukit.read(0x1))
    print(nsukit.bulk_read([0x1, 0x1]))
    print(nsukit.bulk_read([0x1, "ADC NCO频率"]))
    print(nsukit.write(0x1, 0x1))
    print(nsukit.write("ADC NCO频率", 1))
    print(nsukit.bulk_write({0x1: 0x1, 0x2: 0x1}))
    print(nsukit.bulk_write({0x1: 0x1, "ADC NCO频率": 1}))


def test_nsukit_data_tcp():
    """!
    @brief 网络数据流上行测试
    @return:
    """
    event = threading.Event()
    nsukit = NSUKit(TCPCmdUItf, TCPChnlUItf)
    print(nsukit.alloc_buffer(10))
    nsukit.start_stream(target="127.0.0.1", port=6001)
    nsukit.stream_recv(99, 0, 10, 0, event)
    print(nsukit.get_buffer(0, 10))


def test_nsukit_data_pcie():
    """!
    @brief pcie数据流上行测试
    @return:
    """
    event = threading.Event()
    nsukit = NSUKit(TCPCmdUItf, PCIEChnlUItf)
    print(nsukit.alloc_buffer(10))
    nsukit.start_stream(target=0)
    nsukit.stream_recv(0, 0, 10, 0, event)
    print(nsukit.get_buffer(0, 10))


# send 5F5F5F5F 00000031 00000000 18000000 01000000
# recv CFCFCFCF 00000031 00000000 14000000 01000000

# send 5F5F5F5F 03000031 00000000 A8000000 04000000 0000FA42 0F 00 00 00 00 00 00 00 00 88 B3 40 01 00 00 00 00 00 00 00 00 40 5F 40 01 00 00 00 00 00 00 00 00 00 F0 3F 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 03 00 00 00 00 00 00 00 00 88 C3 40 01 00 00 00 00 00 00 00 00 40 5F 40 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00
# recv CFCFCFCF 03000031 00000000 14000000 01000000

# send 5F5F5F5F 09000031 00000000 24000000 00000000 00000000 00 00 F0 3F 00 00 00 00 00 00 00 00
# recv CFCFCFCF 09000031 00000000 14000000 01000000

# send 5F5F5F5F 00000031 00000000 18000000 02000000 01000000
# recv CFCFCFCF 00000031 00000000 14000000 02000000