def check_cs_op(result, func, cargs):
    "Check the status code of a coordinate sequence operation."
    if result == 0:
        raise GEOSException("Could not set value on coordinate sequence")
    else:
        return result