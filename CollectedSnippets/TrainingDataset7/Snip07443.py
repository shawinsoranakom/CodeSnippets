def __init__(self, *args, ordinate=False, get=False, **kwargs):
        if get:
            # Get routines have double parameter passed-in by reference.
            errcheck = check_cs_get
            dbl_param = POINTER(c_double)
        else:
            errcheck = check_cs_op
            dbl_param = c_double

        if ordinate:
            # Get/Set ordinate routines have an extra uint parameter.
            argtypes = [CS_PTR, c_uint, c_uint, dbl_param]
        else:
            argtypes = [CS_PTR, c_uint, dbl_param]

        super().__init__(
            *args, **{**kwargs, "errcheck": errcheck, "argtypes": argtypes}
        )