# Copyright (c) [2023] [Mulan PSL v2]
# [NSUKit] is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

from .base_kit import NSUKit
from .interface.tcp_interface import TCPCmdUItf, TCPChnlUItf
from .interface.serial_interface import SerialCmdUItf
from .interface.pcie_interface import PCIECmdUItf, PCIEChnlUItf


__all__ = ['NSUKit', 'TCPChnlUItf', 'PCIEChnlUItf', 'TCPCmdUItf', 'SerialCmdUItf', 'PCIECmdUItf']

__version_pack__ = (0, 1, 0)

__version__ = '.'.join(str(i) for i in __version_pack__)
