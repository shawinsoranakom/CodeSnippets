def check_pointer(result, func, cargs):
    "Make sure the result pointer is valid."
    if isinstance(result, int):
        result = c_void_p(result)
    if result:
        return result
    else:
        raise GDALException('Invalid pointer returned from "%s"' % func.__name__)