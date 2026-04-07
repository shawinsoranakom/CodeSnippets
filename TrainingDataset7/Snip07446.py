def check_dbl(result, func, cargs):
    """
    Check the status code and returns the double value passed in by reference.
    """
    # Checking the status code
    if result != 1:
        return None
    # Double passed in by reference, return its value.
    return last_arg_byref(cargs)