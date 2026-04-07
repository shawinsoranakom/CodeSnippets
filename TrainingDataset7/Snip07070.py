def check_arg_errcode(result, func, cargs, cpl=False):
    """
    The error code is returned in the last argument, by reference.
    Check its value with `check_err` before returning the result.
    """
    check_err(arg_byref(cargs), cpl=cpl)
    return result