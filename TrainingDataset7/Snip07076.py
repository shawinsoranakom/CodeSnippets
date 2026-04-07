def geom_output(func, argtypes, offset=None):
    """
    Generate a function that returns a Geometry either by reference
    or directly (if the return_geom keyword is set to True).
    """
    # Setting the argument types
    func.argtypes = argtypes

    if not offset:
        # When a geometry pointer is directly returned.
        func.restype = c_void_p
        func.errcheck = check_geom
    else:
        # Error code returned, geometry is returned by-reference.
        func.restype = c_int

        def geomerrcheck(result, func, cargs):
            return check_geom_offset(result, func, cargs, offset)

        func.errcheck = geomerrcheck

    return func