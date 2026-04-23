def main():
    parser = argparse.ArgumentParser(
        description=__doc__.split('\n', 1)[-1])
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='be verbose (currently: print out all symbols)')
    args = parser.parse_args()

    libraries = []

    # static library
    try:
        LIBRARY = pathlib.Path(sysconfig.get_config_var('LIBRARY'))
    except TypeError as exc:
        raise Exception("failed to get LIBRARY sysconfig variable") from exc
    LIBRARY = pathlib.Path(LIBRARY)
    if LIBRARY.exists():
        libraries.append(Library(LIBRARY, is_dynamic=False))

    # dynamic library
    try:
        LDLIBRARY = pathlib.Path(sysconfig.get_config_var('LDLIBRARY'))
    except TypeError as exc:
        raise Exception("failed to get LDLIBRARY sysconfig variable") from exc
    if LDLIBRARY != LIBRARY:
        libraries.append(Library(LDLIBRARY, is_dynamic=True))

    # Check extension modules like _ssl.cpython-310d-x86_64-linux-gnu.so
    libraries.extend(get_extension_libraries())

    smelly_symbols = []
    for library in libraries:
        symbols = get_exported_symbols(library)
        if args.verbose:
            print(f"{library.path}: {len(symbols)} symbol(s) found")
        for symbol in sorted(symbols):
            if args.verbose:
                print("    -", symbol.name)
            if symbol.is_smelly:
                smelly_symbols.append(symbol)

    print()

    if smelly_symbols:
        print(f"Found {len(smelly_symbols)} smelly symbols in total!")
        for symbol in sorted(smelly_symbols):
            print(f"    - {symbol.name} from {symbol.library.path}")
        sys.exit(1)

    print(f"OK: all exported symbols of all libraries",
          f"are prefixed with {' or '.join(map(repr, ALLOWED_PREFIXES))}",
          f"or are covered by exceptions")