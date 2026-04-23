def _setup(namespace: Mapping[str, Any]) -> None:
    global raw_input
    if raw_input is not None:
        return  # don't run _setup twice

    try:
        f_in = sys.stdin.fileno()
        f_out = sys.stdout.fileno()
    except (AttributeError, ValueError):
        return
    if not os.isatty(f_in) or not os.isatty(f_out):
        return

    _wrapper.f_in = f_in
    _wrapper.f_out = f_out

    # set up namespace in rlcompleter, which requires it to be a bona fide dict
    if not isinstance(namespace, dict):
        namespace = dict(namespace)
    _wrapper.config.module_completer = ModuleCompleter(namespace)
    use_basic_completer = (
        not sys.flags.ignore_environment
        and os.getenv("PYTHON_BASIC_COMPLETER")
    )
    completer_cls = RLCompleter if use_basic_completer else FancyCompleter
    _wrapper.config.readline_completer = completer_cls(namespace).complete

    # this is not really what readline.c does.  Better than nothing I guess
    import builtins
    raw_input = builtins.input
    builtins.input = _wrapper.input