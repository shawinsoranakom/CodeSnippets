def void_output(func, argtypes, errcheck=True, cpl=False):
    """
    For functions that don't only return an error code that needs to
    be examined.
    """
    if argtypes:
        func.argtypes = argtypes
    if errcheck:
        # `errcheck` keyword may be set to False for routines that
        # return void, rather than a status code.
        func.restype = c_int
        func.errcheck = partial(check_errcode, cpl=cpl)
    else:
        func.restype = None

    return func