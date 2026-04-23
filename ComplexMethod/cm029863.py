def _partial_new(cls, func, /, *args, **keywords):
    if issubclass(cls, partial):
        base_cls = partial
        if not callable(func):
            raise TypeError("the first argument must be callable")
    else:
        base_cls = partialmethod
        # func could be a descriptor like classmethod which isn't callable
        if not callable(func) and not hasattr(func, "__get__"):
            raise TypeError(f"the first argument {func!r} must be a callable "
                            "or a descriptor")
    if args and args[-1] is Placeholder:
        raise TypeError("trailing Placeholders are not allowed")
    for value in keywords.values():
        if value is Placeholder:
            raise TypeError("Placeholder cannot be passed as a keyword argument")
    if isinstance(func, base_cls):
        pto_phcount = func._phcount
        tot_args = func.args
        if args:
            tot_args += args
            if pto_phcount:
                # merge args with args of `func` which is `partial`
                nargs = len(args)
                if nargs < pto_phcount:
                    tot_args += (Placeholder,) * (pto_phcount - nargs)
                tot_args = func._merger(tot_args)
                if nargs > pto_phcount:
                    tot_args += args[pto_phcount:]
            phcount, merger = _partial_prepare_merger(tot_args)
        else:   # works for both pto_phcount == 0 and != 0
            phcount, merger = pto_phcount, func._merger
        keywords = {**func.keywords, **keywords}
        func = func.func
    else:
        tot_args = args
        phcount, merger = _partial_prepare_merger(tot_args)

    self = object.__new__(cls)
    self.func = func
    self.args = tot_args
    self.keywords = keywords
    self._phcount = phcount
    self._merger = merger
    return self