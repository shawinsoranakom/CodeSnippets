def check_errcode(result, func, cargs, cpl=False):
    """
    Check the error code returned (c_int).
    """
    check_err(result, cpl=cpl)