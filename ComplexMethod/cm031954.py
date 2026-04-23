def _add_cmd_cli(parser, commonspecs, argspecs):
    processors = []
    argspecs = list(commonspecs or ()) + list(argspecs or ())
    for argspec in argspecs:
        if callable(argspec):
            procs = argspec(parser)
            _add_procs(processors, procs)
        else:
            if not argspec:
                raise NotImplementedError
            args = list(argspec)
            if not isinstance(args[-1], str):
                kwargs = args.pop()
                if not isinstance(args[0], str):
                    try:
                        args, = args
                    except (TypeError, ValueError):
                        parser.error(f'invalid cmd args {argspec!r}')
            else:
                kwargs = {}
            parser.add_argument(*args, **kwargs)
            # There will be nothing to process.
    return processors