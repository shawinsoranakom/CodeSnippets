def main(args=None):
    """Run the zipapp command line interface.

    The ARGS parameter lets you specify the argument list directly.
    Omitting ARGS (or setting it to None) works as for argparse, using
    sys.argv[1:] as the argument list.
    """
    import argparse

    parser = argparse.ArgumentParser(color=True)
    parser.add_argument('--output', '-o', default=None,
            help="The name of the output archive. "
                 "Required if SOURCE is an archive.")
    parser.add_argument('--python', '-p', default=None,
            help="The name of the Python interpreter to use "
                 "(default: no shebang line).")
    parser.add_argument('--main', '-m', default=None,
            help="The main function of the application "
                 "(default: use an existing __main__.py).")
    parser.add_argument('--compress', '-c', action='store_true',
            help="Compress files with the deflate method. "
                 "Files are stored uncompressed by default.")
    parser.add_argument('--info', default=False, action='store_true',
            help="Display the interpreter from the archive.")
    parser.add_argument('source',
            help="Source directory (or existing archive).")

    args = parser.parse_args(args)

    # Handle `python -m zipapp archive.pyz --info`.
    if args.info:
        if not os.path.isfile(args.source):
            raise SystemExit("Can only get info for an archive file")
        interpreter = get_interpreter(args.source)
        print("Interpreter: {}".format(interpreter or "<none>"))
        sys.exit(0)

    if os.path.isfile(args.source):
        if args.output is None or (os.path.exists(args.output) and
                                   os.path.samefile(args.source, args.output)):
            raise SystemExit("In-place editing of archives is not supported")
        if args.main:
            raise SystemExit("Cannot change the main function when copying")

    create_archive(args.source, args.output,
                   interpreter=args.python, main=args.main,
                   compressed=args.compress)