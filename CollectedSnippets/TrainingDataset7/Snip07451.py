def check_string(result, func, cargs):
    """
    Error checking for routines that return strings.

    This frees the memory allocated by GEOS at the result pointer.
    """
    if not result:
        raise GEOSException(
            'Error encountered checking string return value in GEOS C function "%s".'
            % func.__name__
        )
    # Getting the string value at the pointer address.
    s = string_at(result)
    # Freeing the memory allocated within GEOS
    free(result)
    return s