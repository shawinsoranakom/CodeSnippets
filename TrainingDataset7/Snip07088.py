def env_func(f, argtypes):
    "For getting OGREnvelopes."
    f.argtypes = argtypes
    f.restype = None
    f.errcheck = check_envelope
    return f