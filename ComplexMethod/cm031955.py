def process_args(args, argv, processors, *, keys=None):
    processors = _flatten_processors(processors)
    ns = vars(args)
    extracted = {}
    if keys is None:
        for process_args in processors:
            for key in process_args(args, argv=argv):
                extracted[key] = ns.pop(key)
    else:
        remainder = set(keys)
        for process_args in processors:
            hanging = process_args(args, argv=argv)
            if isinstance(hanging, str):
                hanging = [hanging]
            for key in hanging or ():
                if key not in remainder:
                    raise NotImplementedError(key)
                extracted[key] = ns.pop(key)
                remainder.remove(key)
        if remainder:
            raise NotImplementedError(sorted(remainder))
    return extracted