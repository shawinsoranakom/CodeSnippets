def object_annotation(obj):
    """
    Return a string to be used for Graphviz nodes.

    The string should be short but as informative as possible.
    """

    def format_sequence(obj):
        body = ','.join(repr(x) if isinstance(x, BASE_TYPES) else type(x).__name__ for x in obj[:8])
        if len(obj) > 8:
            body = f'{body}, ...{len(obj) - 8}'
        return body

    # For basic types, use the repr.
    if isinstance(obj, BASE_TYPES):
        return repr(obj)
    if type(obj).__name__ == 'function':
        return f"function\n{obj.__name__}"
    elif isinstance(obj, types.MethodType):
        try:
            func_name = obj.__func__.__qualname__
        except AttributeError:
            func_name = "<anonymous>"
        return f"instancemethod\n{func_name}"
    elif isinstance(obj, list):
        return f"[{format_sequence(obj)}]"
    elif isinstance(obj, tuple):
        return f"({format_sequence(obj)})"
    elif isinstance(obj, dict):
        return f"dict[{len(obj)}]"
    elif isinstance(obj, types.ModuleType):
        return f"module\n{obj.__name__}"
    elif isinstance(obj, type):
        return f"type\n{obj.__name__}"
    elif isinstance(obj, weakref.ref):
        referent = obj()
        if referent is None:
            return "weakref (dead referent)"
        else:
            return f"weakref to id 0x{id(referent):x}"
    elif isinstance(obj, types.FrameType):
        filename = obj.f_code.co_filename
        if len(filename) > FRAME_FILENAME_LIMIT:
            filename = "..." + filename[-(FRAME_FILENAME_LIMIT - 3):]
        return f"frame\n{filename}:{obj.f_lineno}"
    elif is_cuda_tensor(obj):
        return f"object\n{type(obj).__module__}.{type(obj).__name__} ({obj.shape})"
    else:
        return f"object\n{type(obj).__module__}.{type(obj).__name__}"