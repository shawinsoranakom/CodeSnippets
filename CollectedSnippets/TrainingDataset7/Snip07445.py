def last_arg_byref(args):
    "Return the last C argument's value by reference."
    return args[-1]._obj.value