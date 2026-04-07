def notice_h(fmt, lst):
    fmt, lst = fmt.decode(), lst.decode()
    try:
        warn_msg = fmt % lst
    except TypeError:
        warn_msg = fmt
    logger.warning("GEOS_NOTICE: %s\n", warn_msg)