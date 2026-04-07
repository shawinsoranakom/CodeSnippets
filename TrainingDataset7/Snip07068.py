def check_geom_offset(result, func, cargs, offset=-1):
    "Check the geometry at the given offset in the C parameter list."
    check_err(result)
    geom = ptr_byref(cargs, offset=offset)
    return check_geom(geom, func, cargs)