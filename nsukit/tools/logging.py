import logging

logging = logging


def __init():
    console = logging.StreamHandler()  # 定义console handler
    console.setLevel(logging.DEBUG)  # 定义该handler级别
    formatter = logging.Formatter('%(levelname)s  %(asctime)s  %(message)s')  # 定义该handler格式
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)  # 实例化添加handler
    logging.getLogger().setLevel(logging.DEBUG)


__init()
