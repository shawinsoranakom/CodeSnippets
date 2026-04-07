def int64_output(func, argtypes):
    "Generate a ctypes function that returns a 64-bit integer value."
    func.argtypes = argtypes
    func.restype = c_int64
    return func