def chararray_output(func, argtypes, errcheck=True):
    """For functions that return a c_char_p array."""
    func.argtypes = argtypes
    func.restype = POINTER(c_char_p)
    if errcheck:
        func.errcheck = check_pointer
    return func