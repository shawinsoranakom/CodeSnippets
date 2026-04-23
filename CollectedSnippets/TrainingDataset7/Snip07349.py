def __init__(self, func_name, *, restype=None, errcheck=None, argtypes=None):
        self.func_name = func_name
        if restype is not None:
            self.restype = restype
        if errcheck is not None:
            self.errcheck = errcheck
        if argtypes is not None:
            self.argtypes = argtypes