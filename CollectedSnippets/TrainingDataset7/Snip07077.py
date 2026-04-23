def int_output(func, argtypes, errcheck=None):
    "Generate a ctypes function that returns an integer value."
    func.argtypes = argtypes
    func.restype = c_int
    if errcheck:
        func.errcheck = errcheck
    return func