def _maybe_compile(compiler, source, filename, symbol, flags):
    # Check for source consisting of only blank lines and comments.
    for line in source.split("\n"):
        line = line.strip()
        if line and line[0] != '#':
            break               # Leave it alone.
    else:
        if symbol != "eval":
            source = "pass"     # Replace it with a 'pass' statement

    # Disable compiler warnings when checking for incomplete input.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (SyntaxWarning, DeprecationWarning))
        try:
            compiler(source, filename, symbol, flags=flags)
        except SyntaxError:  # Let other compile() errors propagate.
            try:
                compiler(source + "\n", filename, symbol, flags=flags)
                return None
            except _IncompleteInputError:
                return None
            except SyntaxError:
                pass
                # fallthrough

    return compiler(source, filename, symbol, incomplete_input=False)