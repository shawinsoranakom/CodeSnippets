def units_func(f):
    """
    Create a ctypes function prototype for OSR units functions, e.g.,
    OSRGetAngularUnits, OSRGetLinearUnits.
    """
    return double_output(f, [c_void_p, POINTER(c_char_p)], strarg=True)