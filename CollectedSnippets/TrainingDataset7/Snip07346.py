def error_h(fmt, lst):
    fmt, lst = fmt.decode(), lst.decode()
    try:
        err_msg = fmt % lst
    except TypeError:
        err_msg = fmt
    logger.error("GEOS_ERROR: %s\n", err_msg)