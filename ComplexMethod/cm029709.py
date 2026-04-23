def main():
    import argparse

    description = 'A simple command-line interface for py_compile module.'
    parser = argparse.ArgumentParser(description=description, color=True)
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress error output',
    )
    parser.add_argument(
        'filenames',
        nargs='+',
        help='Files to compile',
    )
    args = parser.parse_args()
    if args.filenames == ['-']:
        filenames = [filename.rstrip('\n') for filename in sys.stdin.readlines()]
    else:
        filenames = args.filenames
    for filename in filenames:
        cfilename = (None if sys.implementation.cache_tag
                     else f"{filename.rpartition('.')[0]}.pyc")
        try:
            compile(filename, cfilename, doraise=True)
        except PyCompileError as error:
            if args.quiet:
                parser.exit(1)
            else:
                parser.exit(1, error.msg)
        except OSError as error:
            if args.quiet:
                parser.exit(1)
            else:
                parser.exit(1, str(error))