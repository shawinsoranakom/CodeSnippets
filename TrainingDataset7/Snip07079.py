def srs_output(func, argtypes):
    """
    Generate a ctypes prototype for the given function with
    the given C arguments that returns a pointer to an OGR
    Spatial Reference System.
    """
    func.argtypes = argtypes
    func.restype = c_void_p
    func.errcheck = check_srs
    return func