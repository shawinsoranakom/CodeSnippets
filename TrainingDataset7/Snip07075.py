def double_output(func, argtypes, errcheck=False, strarg=False, cpl=False):
    "Generate a ctypes function that returns a double value."
    func.argtypes = argtypes
    func.restype = c_double
    if errcheck:
        func.errcheck = partial(check_arg_errcode, cpl=cpl)
    if strarg:
        func.errcheck = check_str_arg
    return func