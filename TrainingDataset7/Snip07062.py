def arg_byref(args, offset=-1):
    "Return the pointer argument's by-reference value."
    return args[offset]._obj.value