def check_srs(result, func, cargs):
    if isinstance(result, int):
        result = c_void_p(result)
    if not result:
        raise SRSException(
            'Invalid spatial reference pointer returned from "%s".' % func.__name__
        )
    return result