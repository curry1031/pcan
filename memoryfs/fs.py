import ctypes

# 加载 C 标准库
libc = ctypes.CDLL("./libc.so.6")

# 定义 malloc 函数的原型
malloc = libc.malloc
malloc.argtypes = [ctypes.c_size_t]
malloc.restype = ctypes.c_void_p

# 定义 free 函数的原型
free = libc.free
free.argtypes = [ctypes.c_void_p]

if __name__ == "__main__":
    # 使用 malloc 分配内存
   ptr = malloc(100)
if ptr:
    print("Memory allocated successfully")
    # 使用分配的内存
    # ...
    # 释放内存
    free(ptr)
else:
    print("Failed to allocate memory")


