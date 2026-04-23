def dis(x=None, *, file=None, depth=None, show_caches=False, adaptive=False,
        show_offsets=False, show_positions=False):
    """Disassemble classes, methods, functions, and other compiled objects.

    With no argument, disassemble the last traceback.

    Compiled objects currently include generator objects, async generator
    objects, and coroutine objects, all of which store their code object
    in a special attribute.
    """
    if x is None:
        distb(file=file, show_caches=show_caches, adaptive=adaptive,
              show_offsets=show_offsets, show_positions=show_positions)
        return
    # Extract functions from methods.
    if hasattr(x, '__func__'):
        x = x.__func__
    # Extract compiled code objects from...
    if hasattr(x, '__code__'):  # ...a function, or
        x = x.__code__
    elif hasattr(x, 'gi_code'):  #...a generator object, or
        x = x.gi_code
    elif hasattr(x, 'ag_code'):  #...an asynchronous generator object, or
        x = x.ag_code
    elif hasattr(x, 'cr_code'):  #...a coroutine.
        x = x.cr_code
    # Perform the disassembly.
    if hasattr(x, '__dict__'):  # Class or module
        items = sorted(x.__dict__.items())
        for name, x1 in items:
            if isinstance(x1, _have_code):
                print("Disassembly of %s:" % name, file=file)
                try:
                    dis(x1, file=file, depth=depth, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
                except TypeError as msg:
                    print("Sorry:", msg, file=file)
                print(file=file)
    elif hasattr(x, 'co_code'): # Code object
        _disassemble_recursive(x, file=file, depth=depth, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
    elif isinstance(x, (bytes, bytearray)): # Raw bytecode
        labels_map = _make_labels_map(x)
        label_width = 4 + len(str(len(labels_map)))
        formatter = Formatter(file=file,
                              offset_width=len(str(max(len(x) - 2, 9999))) if show_offsets else 0,
                              label_width=label_width,
                              show_caches=show_caches)
        arg_resolver = ArgResolver(labels_map=labels_map)
        _disassemble_bytes(x, arg_resolver=arg_resolver, formatter=formatter)
    elif isinstance(x, str):    # Source code
        _disassemble_str(x, file=file, depth=depth, show_caches=show_caches, adaptive=adaptive, show_offsets=show_offsets, show_positions=show_positions)
    else:
        raise TypeError("don't know how to disassemble %s objects" %
                        type(x).__name__)