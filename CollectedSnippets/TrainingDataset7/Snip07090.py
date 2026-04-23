def topology_func(f):
    f.argtypes = [c_void_p, c_void_p]
    f.restype = c_int
    f.errcheck = lambda result, func, cargs: bool(result)
    return f