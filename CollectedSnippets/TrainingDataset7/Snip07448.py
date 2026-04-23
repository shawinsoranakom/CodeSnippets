def check_minus_one(result, func, cargs):
    "Error checking on routines that should not return -1."
    if result == -1:
        raise GEOSException(
            'Error encountered in GEOS C function "%s".' % func.__name__
        )
    else:
        return result