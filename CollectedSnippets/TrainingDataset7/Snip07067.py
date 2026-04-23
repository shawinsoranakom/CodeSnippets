def check_geom(result, func, cargs):
    "Check a function that returns a geometry."
    # OGR_G_Clone may return an integer, even though the
    # restype is set to c_void_p
    if isinstance(result, int):
        result = c_void_p(result)
    if not result:
        raise GDALException(
            'Invalid geometry pointer returned from "%s".' % func.__name__
        )
    return result