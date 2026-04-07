def voidptr_output(func, argtypes, errcheck=True):
    "For functions that return c_void_p."
    func.argtypes = argtypes
    func.restype = c_void_p
    if errcheck:
        func.errcheck = check_pointer
    return func