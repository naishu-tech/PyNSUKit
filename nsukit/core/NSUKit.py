from .interface import CommandTCP, DataTCP
from ..tools.icd_parser import ICDParams


class NSUKit:

    def __init__(self, CommandInterface=None, DataInterface=None, filepath='icd.json'):
        """
        >>>     nsukit = NSUKit(CommandTCP, DataTCP)
        >>>     nsukit.start_command('127.0.0.1')
        >>>     print(nsukit.read('dds0中心频率'))
        >>>     print(nsukit.read(0x01))
        >>>     print(nsukit.bulk_read(['dds0中心频率', 0x01, 'dds0中心频率']))
        >>>     nsukit.start_stream('127.0.0.1')
        >>>     print(nsukit.read_stream(48))
        :param CommandInterface: 指令类
        :param DataInterface: 数据类
        :param filepath: icd文件路径
        """
        if CommandInterface is None or DataInterface is None:
            raise RuntimeError('请传入interface类')
        self.CommandInterface = CommandInterface()
        self.DataInterface = DataInterface()
        self.icd_parser = ICDParams(self, filepath)

    def start_command(self, target=None, *args) -> None:
        self.CommandInterface.accept(target, *args)

    def stop_command(self) -> None:
        self.CommandInterface.close()

    def write(self, addr, value, execute=True) -> list | int:
        if isinstance(addr, str):
            self.icd_parser.set_param(param_name=addr, value=value)
            if execute:
                return self.icd_parser.find_icd_command(addr)
        else:
            return self.CommandInterface.write(addr, value)

    def read(self, addr, default=None) -> int:
        if isinstance(addr, str):
            return self.icd_parser.get_param(addr)
        else:
            return self.CommandInterface.read(addr)

    def bulk_write(self, params: dict) -> list:
        send_len = []
        for param in params:
            if isinstance(param, str):
                send_len.append(self.write(param, params.get(param)))
            else:
                send_len.append(self.CommandInterface.write(param, params.get(param)))
        return send_len

    def bulk_read(self, addrs: list) -> list:
        value = []
        for addr in addrs:
            value.append(self.read(addr))
        return value

    def start_stream(self, ip: str = None):
        self.DataInterface.accept(ip)

    def stop_stream(self):
        self.DataInterface.close()

    def read_stream(self, size: int):
        return self.DataInterface.recv_bytes(size)

    def write_stream(self):
        raise RuntimeError("暂不支持")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_stream()
        self.stop_command()