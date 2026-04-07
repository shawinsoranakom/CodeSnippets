def bool_output(func, argtypes, errcheck=None):
    """Generate a ctypes function that returns a boolean value."""
    func.argtypes = argtypes
    func.restype = c_bool
    if errcheck:
        func.errcheck = errcheck
    return func