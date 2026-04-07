def check_string(result, func, cargs, offset=-1, str_result=False):
    """
    Check the string output returned from the given function, and free
    the string pointer allocated by OGR. The `str_result` keyword
    may be used when the result is the string pointer, otherwise
    the OGR error code is assumed. The `offset` keyword may be used
    to extract the string pointer passed in by-reference at the given
    slice offset in the function arguments.
    """
    if str_result:
        # For routines that return a string.
        ptr = result
        if not ptr:
            s = None
        else:
            s = string_at(result)
    else:
        # Error-code return specified.
        check_err(result)
        ptr = ptr_byref(cargs, offset)
        # Getting the string value
        s = ptr.value
    # Correctly freeing the allocated memory behind GDAL pointer
    # with the VSIFree routine.
    if ptr:
        lgdal.VSIFree(ptr)
    return s