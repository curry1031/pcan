# -*- coding: utf-8 -*-

import os
import VDisk
from memoryfs.VDisk import superBlock,dirTable,D,node,InodeSize,F
pathname = "/root/"  # 表示当前的目录名
ID = -1  # 表示当前目录ID
GlobalPathname = "/root/"  # 表示全部路径
fd = -1
W = None
bufwrite = None
bufread = None
C_F_ID_G = None  # 当前目录的父目录ID


# 初始化函数
def init():
    global pathname, GlobalPathname, fd, W, bufwrite, bufread, C_F_ID_G,ID
    # 将磁盘进行初始化,对块位图，Inode位图不是太了解，于是准备了char类型数组来表示一个字节表示一个块的状态
    # 初始化超级块
    StratDiskAddr = (VDisk.DiskSize)
    superBlock = {
        "Block_Count": VDisk.BlockCount,
        "Inode_Total_Number": 20480 * 32,
        "Inode_Free": 20480 * 32,
        "Block_Size": BlockSize,
        "Block_Free": VDisk.BlockCount - 1 - 1003 - 640 - 20480,
        "First_Block_Addr": bytearray(BlockSize),
        "First_Inode_Addr": bytearray(BlockSize),
        "First_Inode_Block_Addr": bytearray(BlockSize),
        "First_DataBlock_Addr": bytearray(BlockSize),
    }

    superBlock["First_Block_Addr"] = StratDiskAddr + BlockSize
    superBlock["First_Inode_Addr"] = superBlock["First_Block_Addr"] + 1003 * BlockSize
    superBlock["First_Inode_Block_Addr"] = (
        superBlock["First_Inode_Addr"] + 640 * BlockSize
    )
    superBlock["First_DataBlock_Addr"] = (
        superBlock["First_Inode_Block_Addr"] + 20480 * BlockSize
    )

    # 数据块位图，Inode位图初始化
    for i in range(1003 * BlockSize):
        superBlock["First_Block_Addr"][i] = Free

    for i in range(640 * BlockSize):
        superBlock["First_Inode_Addr"][i] = Free

    # 初始化根目录,第一个数据块,由于引进了目录表，所以这里重写
    dirTable = {
        "Current_Dir_Number": 0,
        "dir": [{"InodeId": 0, "Far_InodeId": -1, "free": Use, "FileName": "/root/"}]
        * Max_Dir_Number,
    }
    dirTable["Current_Dir_Number"] = 1

    inode = {"flag": VDisk.D, "FileSize": 0, "Addr1": -1, "Dirrect": [-1] * 5}
    inode["Dirrect"][0] = 0

    # 初始化. ..目录
    dirTable["dir"][1] = {
        "InodeId": 1,
        "Far_InodeId": dirTable["dir"][0]["InodeId"],
        "free": Use,
        "FileName": ".",
    }
    inode1 = {"flag": VDisk.D, "FileSize": 0, "Addr1": -1, "Dirrect": [-1] * 5}
    inode1["Dirrect"][0] = 0

    dirTable["dir"][2] = {
        "InodeId": 2,
        "Far_InodeId": dirTable["dir"][0]["InodeId"],
        "free": Use,
        "FileName": "..",
    }
    inode2 = {"flag": VDisk.D, "FileSize": 0, "Addr1": -1, "Dirrect": [-1] * 5}
    inode2["Dirrect"][0] = 0

    superBlock["Block_Free"] -= 1
    superBlock["First_Block_Addr"][0] = Use

    pathname = "/root/"
    GlobalPathname = "/root/"


# -*- coding: utf-8 -*-


# 检查同名的是否文件与目录
def check(C_Inode_Id, flag):
    F_O_D = VDisk.node[C_Inode_Id]["flag"]
    if flag == F_O_D:
        return -1
    else:
        return 0


# 分配inode号码
def get_free_inode():
    for i in range(640 * BlockSize):
        if VDisk.superBlock["First_Inode_Addr"][i] == Free:
            return i
    return -1


# 创建文件 成功返回0 失败返回-1
# 后续会更新一次性创建多个文件
def touch(filename):
    global ID
    # 检查是否重名
    if ID < 0:
        ID = searchID(pathname)
        if ID == -1:
            print("this dir is not existed")
            return -1

    C_Inode_Id = -1
    # 检查是否重名
    for i in range(1003 * BlockSize):
        if (
            VDisk.superBlock["First_Block_Addr"][i] == Use
            and VDisk.dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = VDisk.dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == filename
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    C_Inode_Id = dirTable1["dir"][j]["InodeId"]
                    break
        if VDisk.superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = VDisk.dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == filename
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    C_Inode_Id = dirTable1["dir"][j]["InodeId"]
                    break

    if C_Inode_Id != -1:
        C_Inode_Id = check(C_Inode_Id, VDisk.F)
        if C_Inode_Id == -1:
            print("this file is already existed")
            return -1

    # 分配磁盘块
    for i in range(1003 * BlockSize):
        if (
            VDisk.superBlock["First_Block_Addr"][i] == Free
            and VDisk.dirTable[i]["Current_Dir_Number"] >= 0
        ):
            dirTable1 = VDisk.dirTable[i]
            for k in range(Max_Dir_Number):
                if dirTable1["dir"][k]["free"] == Free:
                    dirTable1["dir"][k]["FileName"] = filename
                    dirTable1["dir"][k]["InodeId"] = get_free_inode()
                    dirTable1["dir"][k]["Far_InodeId"] = ID
                    dirTable1["dir"][k]["free"] = Use

                    if (
                        dirTable1["dir"][k]["InodeId"]
                        > VDisk.superBlock["Inode_Total_Number"]
                    ):
                        dirTable1["dir"][k]["free"] = Free
                        print("the inode_block is full")
                        return -1
                    else:
                        inode = (
                            VDisk.superBlock["First_Inode_Block_Addr"]
                            + dirTable1["dir"][k]["InodeId"] * VDisk.InodeSize
                        )
                        dirTable1["Current_Dir_Number"] += 1
                        inode["flag"] = VDisk.F
                        inode["Addr1"] = -1
                        inode["FileSize"] = 0
                        inode["Dirrect"][0] = get_free_block()
                        if inode["Dirrect"][0] == -1:
                            dirTable1["Current_Dir_Number"] -= 1
                            print("the Block is full")
                            return -1

                        VDisk.superBlock["First_Inode_Addr"][
                            dirTable1["dir"][k]["InodeId"]
                        ] = Use
                        VDisk.superBlock["Inode_Free"] -= 1
                        if dirTable1["dir"][Max_Dir_Number - 1]["free"] == Use:
                            VDisk.superBlock["First_Block_Addr"][i] = Use

                    return 0

    print("your input is wrong, please input again")
    return -1


# 分配空闲的数据块 成功返回相应的块号 失败返回 -1
def get_free_block():
    # 分配磁盘块
    for i in range(1003 * BlockSize):
        if VDisk.superBlock["First_Block_Addr"][i] == Free:
            if dirTable[i]["Current_Dir_Number"] > 0:
                continue
            else:
                superBlock["First_Block_Addr"][i] = Use
                superBlock["Block_Free"] -= 1
                return i
    return -1


# 打开文件 成功返回文件的inode号即文件描述符 不直接返回块号 失败返回 -1 是否可以连续打开同一个文件？？？
def open(filename):
    global ID
    # 通过文件名在目录目录块中找到相应的目录项
    inodeId = 0
    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == filename
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    inodeId = dirTable1["dir"][j]["InodeId"]
                    break
        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if dirTable1["dir"][j]["FileName"] == filename:
                    inodeId = dirTable1["dir"][j]["InodeId"]
                    break

    if inodeId == 0:
        print("this file is not existed")
        return -1
    else:
        if node[inodeId]["flag"] == D:
            print("this is a dir,can not open")
            return -1
        else:
            return inodeId


def format():
    init()
    # strcpy(pathname,"/root/")
    #  GlobalPathname = "/root/"


# 查找本层目录的ID
def searchID(currentdir):
    name = currentdir
    # strcpy(name, currentdir)
    for i in range(640 * BlockSize):
        if superBlock["First_Inode_Addr"][i] == Use:
            inode = node[i]
            if inode["flag"] == D:
                j = inode["Dirrect"][0]
                dirTable1 = dirTable[j]
                for k in range(Max_Dir_Number):
                    if (
                        dirTable1["dir"][k]["FileName"] == name
                        and dirTable1["dir"][k]["free"] == Use
                    ):
                        if node[dirTable1["dir"][k]["InodeId"]]["flag"] == D:
                            ID = dirTable1["dir"][k]["InodeId"]
                            if ID != C_F_ID_G:
                                continue
                            return ID
    return -1


# 创建目录成功返回0 失败返回 -1
# 后续会增加一次性创建多个文件
def mkdir(dirname):
    global ID
    C_Inode_Id = -1
    # 获得当前目录以及目录ID
    if ID < 0:
        ID = searchID(pathname)

    # 检查是否重名
    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == dirname
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                ):
                    C_Inode_Id = dirTable1["dir"][j]["InodeId"]
                    break
        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == dirname
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                ):
                    C_Inode_Id = dirTable1["dir"][j]["InodeId"]
                    break

    # 检查是否重名
    if C_Inode_Id != -1:
        C_Inode_Id = check(C_Inode_Id, D)
        if C_Inode_Id == -1:
            print("this dir is already existed")
            return -1

    # 这里创建目录没有考虑到 . .. 目录？？？
    # 不重名，则从空闲的目录表中分配该目录,与文件创建不同的是，文件需要分配额外的数据块空间而目录不需要所以目录的inode中的direct[0]就是所在目录块
    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Free
            and dirTable[i]["Current_Dir_Number"] >= 0
        ):
            dirTable1 = dirTable[i]
            for k in range(Max_Dir_Number):
                if dirTable1["dir"][k]["free"] == Free:
                    dirTable1["dir"][k]["FileName"] = dirname
                    dirTable1["dir"][k]["InodeId"] = get_free_inode()
                    dirTable1["dir"][k]["Far_InodeId"] = ID
                    dirTable1["dir"][k]["free"] = Use

                    # 3.从Inode块中建立inode，inode位图相应位置置1，且可用的inode-1
                    if (
                        dirTable1["dir"][k]["InodeId"]
                        > superBlock["Inode_Total_Number"]
                    ):
                        dirTable1["dir"][k]["free"] = Free
                        print("the inode_block is full")
                        return -1
                    else:
                        inode = (
                            superBlock["First_Inode_Block_Addr"]
                            + dirTable1["dir"][k]["InodeId"] * InodeSize
                        )
                        dirTable1["Current_Dir_Number"] += 1
                        inode["flag"] = D
                        inode["Addr1"] = -1
                        inode["FileSize"] = 0
                        inode["Dirrect"][0] = i

                        superBlock["First_Inode_Addr"][
                            dirTable1["dir"][k]["InodeId"]
                        ] = Use
                        superBlock["Inode_Free"] -= 1
                        if dirTable1["dir"][Max_Dir_Number - 1]["free"] == Use:
                            superBlock["First_Block_Addr"][i] = Use

                    return 0

    print("something goes wrong, you can format your system")
    return -1


# -*- coding: utf-8 -*-


# 删除文件操作，成功返回0，失败返回-1
# 这里需要维护一个记录 inode 使用情况的数组 inodeUse，用于重复利用释放的 inode
def rm(filename):
    global ID
    if ID < 0:
        ID = searchID(pathname)
    i = 0
    # 从数据位示图中获取目录块信息
    node = superBlock["First_Inode_Block_Addr"]
    dirTable = superBlock["First_DataBlock_Addr"]
    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == filename
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    currentID = dirTable1["dir"][j]["InodeId"]
                    if node[currentID]["flag"] == F:
                        superBlock["First_Block_Addr"][i] = Free
                        superBlock["First_Inode_Addr"][currentID] = Free
                        inode = node[currentID]
                        dirTable1["Current_Dir_Number"] -= 1
                        currentID = inode["Dirrect"][0]
                        superBlock["First_Block_Addr"][currentID] = Free
                        dirTable1["dir"][j]["InodeId"] = -1
                        dirTable1["dir"][j]["FileName"] = ""
                        dirTable1["dir"][j]["free"] = Free
                        dirTable1["dir"][j]["Far_InodeId"] = -1
                        superBlock["Inode_Free"] += 1
                        superBlock["Block_Free"] += 1
                        return 0
                    else:
                        print("this file  is not existed")
                        return -1

        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == filename
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    currentID = dirTable1["dir"][j]["InodeId"]
                    if node[currentID]["flag"] == F:
                        superBlock["First_Inode_Addr"][currentID] = Free
                        inode = node[currentID]
                        dirTable1["Current_Dir_Number"] -= 1
                        currentID = inode["Dirrect"][0]
                        superBlock["First_Block_Addr"][currentID] = Free
                        dirTable1["dir"][j]["InodeId"] = -1
                        dirTable1["dir"][j]["FileName"] = ""
                        dirTable1["dir"][j]["free"] = Free
                        dirTable1["dir"][j]["Far_InodeId"] = -1
                        superBlock["Inode_Free"] += 1
                        superBlock["Block_Free"] += 1
                        return 0
                    else:
                        print("this file is not existed")
                        return -1

    print("your operation is wrong, please input again")
    return -1


# 删除目录操作，成功返回0，失败返回-1
# 后续会增加一次性删除多个目录
def rmdir(dirname):
    global pathname, GlobalPathname, fd, W, bufwrite, bufread, C_F_ID_G, ID
    C_I_D = -1
    C_B_ID = -1
    D_B_index = (
        -1
    )  # 表示找到的目录的 inode，与当前所在的块，D_B_index表示目录在改目录快中的索引位置
    # 与文件删除相似，不过要判断要删除的目录是否含有子目录或文件
    # 首先通过目录名找到对应的目录块所在位置
    if  ID < 0:
        ID = searchID(pathname)
    i = 0
    # 从数据位示图中获取目录块信息
    node = superBlock["First_Inode_Block_Addr"]
    dirTable = superBlock["First_DataBlock_Addr"]
    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == dirname
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    C_B_ID = i
                    D_B_index = j
                    C_I_D = dirTable1["dir"][j]["InodeId"]

        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == dirname
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                    and dirTable1["dir"][j]["free"] == Use
                ):
                    C_B_ID = i
                    D_B_index = j
                    C_I_D = dirTable1["dir"][j]["InodeId"]

    if C_I_D == -1 and C_B_ID == -1 and D_B_index == -1:
        print("this dir is not existed")
        return -1

    # 判断该目录下是否存在子目录或文件
    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["free"] == Use
                    and dirTable1["dir"][j]["Far_InodeId"] == C_I_D
                ):
                    print("this dir has some files or dirs, which could not be deleted")
                    return -1

        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["free"] == Use
                    and dirTable1["dir"][j]["Far_InodeId"] == C_I_D
                ):
                    print("this dir has some files or dirs, which could not be deleted")
                    return -1

    # 删除目录
    dirTable1 = dirTable[C_B_ID]
    if dirTable1["Current_Dir_Number"] == Max_Dir_Number:
        if node[C_I_D]["flag"] == D:
            superBlock["First_Block_Addr"][C_B_ID] = Free
            dirTable1["Current_Dir_Number"] -= 1
            dirTable1["dir"][D_B_index]["free"] = Free
            dirTable1["dir"][D_B_index]["FileName"] = ""
            superBlock["First_Inode_Addr"][C_I_D] = Free
            superBlock["Inode_Free"] += 1
            return 0
        else:
            print("this is a file, not a dir")
            return -1
    else:
        if node[C_I_D]["flag"] == D:
            dirTable1["Current_Dir_Number"] -= 1
            dirTable1["dir"][D_B_index]["FileName"] = ""
            dirTable1["dir"][D_B_index]["free"] = Free
            superBlock["First_Inode_Addr"][C_I_D] = Free
            superBlock["Inode_Free"] += 1
            return 0
        else:
            print("this is a file, not a dir")
            return -1


# cd 命令，成功返回0，失败返回-1
def cd(dirname):
    global ID, C_F_ID_G, pathname, GlobalPathname
    if ID < 0:
        ID = searchID(pathname)
        if ID == -1:
            print("this dir is not existed")
            return -1

    # 进入上一层目录..与本层目录. ，这里在进行目录创建时并没有创建. ..，要实现需要再目录创建时进行修改,这里作为第一版开发暂不进行实现，后续更新会进行增加  ?????
    node = superBlock["First_Inode_Block_Addr"]
    dirTable = superBlock["First_DataBlock_Addr"]
    dirTable2 = dirTable[node[ID]["Dirrect"][0]]
    for j in range(Max_Dir_Number):
        if (
            dirTable2["dir"][j]["FileName"] == pathname
            and dirTable2["dir"][j]["free"] == Use
            and node[dirTable2["dir"][j]["InodeId"]]["flag"] == D
        ):
            if dirTable2["dir"][j]["InodeId"] == C_F_ID_G:
                C_F_ID = dirTable2["dir"][j]["Far_InodeId"]
                break
            else:
                continue

    if C_F_ID == -1:
        return -1
        print("can not cd this dir")

    # 进入的目录属于直接关系
    # 判断是否属于直接上下层关系
    for i in range(1003 * BlockSize):
        # 如果进入的是根目录
        if dirname == "/root/":
            pathname = "/root/"
            GlobalPathname = "/root/"
            C_F_ID_G = 0
            ID = -1
            return 0

        # 进入的不是根目录
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == dirname
                    and dirTable1["dir"][j]["free"] == Use
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                ):
                    if node[dirTable1["dir"][j]["InodeId"]]["flag"] == D:
                        C_F_ID_G = dirTable1["dir"][j]["InodeId"]
                        pathname = dirTable1["dir"][j]["FileName"]
                        GlobalPathname += pathname
                        GlobalPathname += "/"
                        ID = -1
                        return 0

                # 如果进入的是本层的上一层
                if (
                    dirname == ".."
                    and dirTable1["dir"][j]["free"] == Use
                    and C_F_ID == 0
                ):
                    pathname = "/root/"
                    GlobalPathname = "/root/"
                    C_F_ID_G = 0
                    ID = -1
                    return 0
                else:
                    if (
                        dirname == ".."
                        and dirTable1["dir"][j]["free"] == Use
                        and C_F_ID == dirTable1["dir"][j]["InodeId"]
                    ):
                        GlobalPathname = GlobalPathname[:-1]
                        GlobalPathname = GlobalPathname[: -len(pathname)]
                        pathname = dirTable1["dir"][j]["FileName"]
                        C_F_ID_G = C_F_ID
                        ID = -1
                        return 0

        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["FileName"] == dirname
                    and dirTable1["dir"][j]["free"] == Use
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                ):
                    if node[dirTable1["dir"][j]["InodeId"]]["flag"] == D:
                        C_F_ID_G = dirTable1["dir"][j]["InodeId"]
                        pathname = dirTable1["dir"][j]["FileName"]
                        GlobalPathname += pathname
                        GlobalPathname += "/"
                        ID = -1
                        return 0

                # 如果进入的是本层的上一层
                if (
                    dirname == ".."
                    and dirTable1["dir"][j]["free"] == Use
                    and C_F_ID == 0
                ):
                    pathname = "/root/"
                    GlobalPathname = "/root/"
                    C_F_ID_G = 0
                    ID = -1
                    return 0
                else:
                    if (
                        dirname == ".."
                        and dirTable1["dir"][j]["free"] == Use
                        and C_F_ID == dirTable1["dir"][j]["InodeId"]
                    ):
                        GlobalPathname = GlobalPathname[:-1]
                        GlobalPathname = GlobalPathname[: -len(pathname)]
                        pathname = dirTable1["dir"][j]["FileName"]
                        C_F_ID_G = C_F_ID
                        ID = -1
                        return 0

    # 进入的目录属于间接关系，这部分实现有点麻烦，涉及到全局路径,作为第一版暂时不考虑开发实现 ？？？？？
    print("your input is wrong, please input again")
    return -1


# ls 命令，显示当前目录下的所有内容
def ls():
    global ID, pathname, GlobalPathname
    if ID < 0:
        ID = searchID(pathname)
        if ID == -1:
            return -1

    # 首先当前目录的ID已经拿到，要做的就是找目录块中 FartherInodeID 属于 ID 的目录与文件即可，如果在设计结构式加上 son_id 将会更快，后续会考虑更新
    node = superBlock["First_Inode_Block_Addr"]
    dirTable = superBlock["First_DataBlock_Addr"]

    for i in range(1003 * BlockSize):
        if (
            superBlock["First_Block_Addr"][i] == Use
            and dirTable[i]["Current_Dir_Number"] == Max_Dir_Number
        ):
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["free"] == Use
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                ):
                    if node[dirTable1["dir"][j]["InodeId"]]["flag"] == 1:
                        print(
                            dirTable1["dir"][j]["FileName"]
                            + "\t\t\t\t\t\t\t\t\tfile\t\t"
                            + str(node[dirTable1["dir"][j]["InodeId"]]["FileSize"])
                            + "B"
                        )
                    else:
                        print(dirTable1["dir"][j]["FileName"] + "\t\t\t\t\t\t\t\t\tdir")
        if superBlock["First_Block_Addr"][i] == Free:
            dirTable1 = dirTable[i]
            for j in range(Max_Dir_Number):
                if (
                    dirTable1["dir"][j]["free"] == Use
                    and dirTable1["dir"][j]["Far_InodeId"] == ID
                ):
                    if node[dirTable1["dir"][j]["InodeId"]]["flag"] == 1:
                        print(
                            dirTable1["dir"][j]["FileName"]
                            + "\t\t\t\t\t\t\t\t\tfile\t\t"
                            + str(node[dirTable1["dir"][j]["InodeId"]]["FileSize"])
                            + "B"
                        )
                    else:
                        print(dirTable1["dir"][j]["FileName"] + "\t\t\t\t\t\t\t\t\tdir")

    return 0


import sys

BlockSize = 1024
Max_Text_Count = 1024
Max_Dir_Number = 10
Use = 1
Free = 0

# 全局变量
fd = -1
ID = -1
C_F_ID_G = -1
GlobalPathname = ""
bufread = ""
bufwrite = ""
StratDiskAddr = ""
W = ""


class SuperBlock:
    def __init__(self):
        self.First_Block_Addr = []
        self.First_Inode_Addr = []
        self.First_DataBlock_Addr = []
        self.First_Inode_Block_Addr = []
        self.Inode_Free = 0
        self.Block_Free = 0


class Inode:
    def __init__(self):
        self.Dirrect = [0] * 5
        self.flag = 0
        self.FileSize = 0


class DirTable:
    def __init__(self):
        self.Current_Dir_Number = 0
        self.dir = []
        for _ in range(Max_Dir_Number):
            self.dir.append(DirEntry())


class DirEntry:
    def __init__(self):
        self.FileName = ""
        self.InodeId = -1
        self.Far_InodeId = -1
        self.free = Free


def get_free_block():
    # 返回一个可用的数据块
    pass


def searchID(pathname):
    # 根据路径名查找对应的ID
    pass


def mkdir(dirname):
    # 创建文件夹
    pass


def touch(filename):
    # 创建文件
    pass


def rm(filename):
    # 删除文件
    pass


def rmdir(dirname):
    # 删除文件夹
    pass


def cd(dirname):
    # 进入目录
    pass


def ls():
    # 显示当前目录下的所有内容
    pass


def read(fd, count):
    # 读文件
    pass


def write(fd, buf, count):
    # 写文件
    pass


def exit():
    # 退出系统
    pass


def help():
    # 显示帮助信息
    pass


def close(filename):
    # 关闭文件
    pass


def main():
    # 主函数
    pass
