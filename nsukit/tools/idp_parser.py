"""!
IDP(InitDeviceParam): 以字符串描述某一具体的协议接口参数信息
例如：
某一物理接口采用 tcp协议，ip为127.0.0.1，端口为5001，
则其IDP为  tcp://127.0.0.1:5001
"""
import enum


class Mode:
    pass


def idp2dict(path: str, mode) -> dict:
    """!
    将IDP转换为可Dict
    @param path:
    @param mode:
    @return:
    """
    if path.find('://') == -1:
        raise ValueError(f'{path} must contain the keyword ://')
    pack = path.split(':')
