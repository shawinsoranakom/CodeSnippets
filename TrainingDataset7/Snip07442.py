def check_cs_get(result, func, cargs):
    "Check the coordinate sequence retrieval."
    check_cs_op(result, func, cargs)
    # Object in by reference, return its value.
    return last_arg_byref(cargs)