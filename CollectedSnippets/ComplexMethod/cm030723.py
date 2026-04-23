def stderr_to_parser_error(parse_args, *args, **kwargs):
    # if this is being called recursively and stderr or stdout is already being
    # redirected, simply call the function and let the enclosing function
    # catch the exception
    if isinstance(sys.stderr, StdIOBuffer) or isinstance(sys.stdout, StdIOBuffer):
        return parse_args(*args, **kwargs)

    # if this is not being called recursively, redirect stderr and
    # use it as the ArgumentParserError message
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StdIOBuffer()
    sys.stderr = StdIOBuffer()
    try:
        try:
            result = parse_args(*args, **kwargs)
            for key in list(vars(result)):
                attr = getattr(result, key)
                if attr is sys.stdout:
                    setattr(result, key, old_stdout)
                elif attr is sys.stdout.buffer:
                    setattr(result, key, getattr(old_stdout, 'buffer', BIN_STDOUT_SENTINEL))
                elif attr is sys.stderr:
                    setattr(result, key, old_stderr)
                elif attr is sys.stderr.buffer:
                    setattr(result, key, getattr(old_stderr, 'buffer', BIN_STDERR_SENTINEL))
            return result
        except SystemExit as e:
            code = e.code
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            raise ArgumentParserError(
                "SystemExit", stdout, stderr, code) from None
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr