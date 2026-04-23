def check_sized_string(result, func, cargs):
    """
    Error checking for routines that return explicitly sized strings.

    This frees the memory allocated by GEOS at the result pointer.
    """
    if not result:
        raise GEOSException(
            'Invalid string pointer returned by GEOS C function "%s"' % func.__name__
        )
    # A c_size_t object is passed in by reference for the second
    # argument on these routines, and its needed to determine the
    # correct size.
    s = string_at(result, last_arg_byref(cargs))
    # Freeing the memory allocated within GEOS
    free(result)
    return s