def binutils_get_exported_symbols(library, dynamic=False):
    """Retrieve exported symbols using the nm(1) tool from binutils"""
    # Only look at dynamic symbols
    args = ["nm", "--no-sort"]
    if dynamic:
        args.append("--dynamic")
    args.append(library)
    proc = subprocess.run(args, stdout=subprocess.PIPE, encoding='utf-8')
    if proc.returncode:
        sys.stdout.write(proc.stdout)
        sys.exit(proc.returncode)

    stdout = proc.stdout.rstrip()
    if not stdout:
        raise Exception("command output is empty")

    for line in stdout.splitlines():
        # Split line '0000000000001b80 D PyTextIOWrapper_Type'
        if not line:
            continue

        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            continue

        symbol = parts[-1]
        if MACOS and symbol.startswith("_"):
            yield symbol[1:]
        else:
            yield symbol