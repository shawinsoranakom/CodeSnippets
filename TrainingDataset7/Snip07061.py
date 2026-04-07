def function(name, args, restype):
    func = std_call(name)
    func.argtypes = args
    func.restype = restype
    return func