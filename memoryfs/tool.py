# -*- coding: utf-8 -*-

# 定义命令选项
options = ["mkdir", "touch", "rmdir", "rm", "open", "write", "read", "cd", "close"]

# 空格处理函数
def process_space(text):
    return " ".join(text.split())

# 命令识别函数
def check_option(buf):
    tmp = buf.strip()
    for i, opt in enumerate(options):
        if opt == tmp:
            return i + 1
    return -1
