def get_exported_symbols(library):
    # Only look at dynamic symbols
    args = ['nm', '--no-sort']
    if library.is_dynamic:
        args.append('--dynamic')
    args.append(library.path)
    proc = subprocess.run(args, stdout=subprocess.PIPE, encoding='utf-8')
    if proc.returncode:
        print("+", args)
        sys.stdout.write(proc.stdout)
        sys.exit(proc.returncode)

    stdout = proc.stdout.rstrip()
    if not stdout:
        raise Exception("command output is empty")

    symbols = []
    for line in stdout.splitlines():
        if not line:
            continue

        # Split lines like  '0000000000001b80 D PyTextIOWrapper_Type'
        parts = line.split(maxsplit=2)
        # Ignore lines like '                 U PyDict_SetItemString'
        # and headers like 'pystrtod.o:'
        if len(parts) < 3:
            continue

        symbol = Symbol(name=parts[-1], type=parts[1], library=library)
        if not symbol.is_local:
            symbols.append(symbol)

    return symbols