def _get_builtins_helper():
    builtins = []
    for fn, _builtin_name in torch.jit._builtins._builtin_ops:
        mod = inspect.getmodule(fn)

        if not hasattr(fn, "__name__"):
            # typing classes
            continue
        if not mod:
            continue
        if _hidden(fn.__name__) or _hidden(fn.__qualname__) or _hidden(mod.__name__):
            # skip internal-only methods
            continue

        if "torch._C" in mod.__name__:
            continue

        builtins.append((fn, _builtin_name))

    return builtins