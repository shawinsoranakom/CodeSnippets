def pnt_func(f):
    "For accessing point information."
    return double_output(f, [c_void_p, c_int])