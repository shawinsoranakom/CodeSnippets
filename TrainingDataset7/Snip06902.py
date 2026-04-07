def check_err(code, cpl=False):
    """
    Check the given CPL/OGRERR and raise an exception where appropriate.
    """
    err_dict = CPLERR_DICT if cpl else OGRERR_DICT

    if code == ERR_NONE:
        return
    elif code in err_dict:
        e, msg = err_dict[code]
        raise e(msg)
    else:
        raise GDALException('Unknown error code: "%s"' % code)