def ptr_byref(args, offset=-1):
    "Return the pointer argument passed in by-reference."
    return args[offset]._obj