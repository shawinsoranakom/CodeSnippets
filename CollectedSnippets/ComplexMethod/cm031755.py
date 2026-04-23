def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hVo:',
                                   ['help', 'version', 'output-file='])
    except getopt.error as msg:
        usage(1, msg)

    outfile = None
    # parse options
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-V', '--version'):
            print("msgfmt.py", __version__)
            sys.exit(0)
        elif opt in ('-o', '--output-file'):
            outfile = arg
    # do it
    if not args:
        print('No input file given', file=sys.stderr)
        print("Try `msgfmt --help' for more information.", file=sys.stderr)
        return

    for filename in args:
        make(filename, outfile)