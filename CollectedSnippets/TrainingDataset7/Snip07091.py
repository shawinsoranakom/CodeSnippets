def srs_double(f):
    """
    Create a function prototype for the OSR routines that take
    the OSRSpatialReference object and return a double value.
    """
    return double_output(f, [c_void_p, POINTER(c_int)], errcheck=True)