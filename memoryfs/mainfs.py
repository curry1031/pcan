import sys
import tool
import FileOperate
from FileOperate import pathname,GlobalPathname
# 全局变量
Flen = 0
from tool import check_option
from memoryfs.FileOperate import ls,init,mkdir,touch,rmdir,write,cd,read,bufread,close,rm
def main():
    global pathname,GlobalPathname
    init()
    pathname = "/root/"
    GlobalPathname = "/root/"
    ls()
    print("--------------------------------- Memory File System ---------------------------------")
    print("if this is your first use my system, you can input help to get some commands, the length of commands is limit to 80, please type it carefully!")

    while True:
        input_str = input(GlobalPathname)
        if not input_str:
            continue

        input_list = input_str.split(" ")

        # 处理不带参数的命令
        if input_list[0] == "ls":
            if ls() == -1:
                print("something goes wrong")
        elif input_list[0] == "format":
            format()
            print("format successfully")
        elif input_list[0] == "help":
            help()
        elif input_list[0] == "exit":
            exit()
            print("thanks to use this system, have a good luck!")
            break
        elif input_list[0] in ["mkdir", "rm", "touch", "rmdir", "open", "cd"]:
            print("wrong command, please input again!")
        else:
            # 处理带参数的命令
            Select = check_option(input_list[0])
            if Select == 1:
                if fd != -1:
                    print("you need close the file")
                    continue
                if mkdir(input_list[1]) == 0:
                    print("the dir is successful")
            elif Select == 2:
                if fd != -1:
                    print("you need close the file")
                    continue
                if touch(input_list[1]) == 0:
                    print("the file is successful")
            elif Select == 3:
                if fd != -1:
                    print("you need close the file")
                    continue
                if rmdir(input_list[1]) == 0:
                    print("the dir is deleted")
            elif Select == 4:
                if fd != -1:
                    print("you need close the file")
                    continue
                if rm(input_list[1]) == 0:
                    print("the file is deleted")
            elif Select == 5:
                fd = open(input_list[1])
                if fd != -1:
                    print("open successfully")
            elif Select == 6:
                if fd == -1:
                    print("you need to open this file")
                    continue
                else:
                    print("please write your words or sentences here:")
                    input_str = input()
                    Flen = len(input_str)
                    if write(fd, input_str, Flen) == Flen:
                        print("write successfully")
            elif Select == 7:
                if fd == -1:
                    print("you need to open this file")
                    continue
                else:
                    read(fd, input_list[1], 0)
                    print(bufread)
            elif Select == 8:
                if fd != -1:
                    print("you need close the file")
                    continue
                cd(input_list[1])
            elif Select == 9:
                if close(input_list[1]) == 0:
                    print("the file is closed successfully")
            else:
                print("wrong command, please input again!")

if __name__ == "__main__":
    main()
