def main():
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'ac::d:DEhk:Kno:p:S:Vvw:x:X:',
            ['extract-all', 'add-comments=?', 'default-domain=', 'escape',
             'help', 'keyword=', 'no-default-keywords',
             'add-location', 'no-location', 'output=', 'output-dir=',
             'style=', 'verbose', 'version', 'width=', 'exclude-file=',
             'docstrings', 'no-docstrings',
             ])
    except getopt.error as msg:
        usage(1, msg)

    # for holding option values
    class Options:
        # constants
        GNU = 1
        SOLARIS = 2
        # defaults
        extractall = 0 # FIXME: currently this option has no effect at all.
        escape = 0
        keywords = []
        outpath = ''
        outfile = 'messages.pot'
        writelocations = 1
        locationstyle = GNU
        verbose = 0
        width = 78
        excludefilename = ''
        docstrings = 0
        nodocstrings = {}
        comment_tags = set()

    options = Options()
    locations = {'gnu' : options.GNU,
                 'solaris' : options.SOLARIS,
                 }
    no_default_keywords = False
    # parse options
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(0)
        elif opt in ('-a', '--extract-all'):
            print("DeprecationWarning: -a/--extract-all is not implemented and will be removed in a future version",
                  file=sys.stderr)
            options.extractall = 1
        elif opt in ('-c', '--add-comments'):
            options.comment_tags.add(arg)
        elif opt in ('-d', '--default-domain'):
            options.outfile = arg + '.pot'
        elif opt in ('-E', '--escape'):
            options.escape = 1
        elif opt in ('-D', '--docstrings'):
            options.docstrings = 1
        elif opt in ('-k', '--keyword'):
            options.keywords.append(arg)
        elif opt in ('-K', '--no-default-keywords'):
            no_default_keywords = True
        elif opt in ('-n', '--add-location'):
            options.writelocations = 1
        elif opt in ('--no-location',):
            options.writelocations = 0
        elif opt in ('-S', '--style'):
            options.locationstyle = locations.get(arg.lower())
            if options.locationstyle is None:
                usage(1, f'Invalid value for --style: {arg}')
        elif opt in ('-o', '--output'):
            options.outfile = arg
        elif opt in ('-p', '--output-dir'):
            options.outpath = arg
        elif opt in ('-v', '--verbose'):
            options.verbose = 1
        elif opt in ('-V', '--version'):
            print(f'pygettext.py (xgettext for Python) {__version__}')
            sys.exit(0)
        elif opt in ('-w', '--width'):
            try:
                options.width = int(arg)
            except ValueError:
                usage(1, f'--width argument must be an integer: {arg}')
        elif opt in ('-x', '--exclude-file'):
            options.excludefilename = arg
        elif opt in ('-X', '--no-docstrings'):
            fp = open(arg)
            try:
                while 1:
                    line = fp.readline()
                    if not line:
                        break
                    options.nodocstrings[line[:-1]] = 1
            finally:
                fp.close()

    options.comment_tags = tuple(options.comment_tags)

    # calculate escapes
    make_escapes(not options.escape)

    # calculate all keywords
    try:
        options.keywords = process_keywords(
            options.keywords,
            no_default_keywords=no_default_keywords)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    # initialize list of strings to exclude
    if options.excludefilename:
        try:
            with open(options.excludefilename) as fp:
                options.toexclude = fp.readlines()
        except OSError:
            print(f"Can't read --exclude-file: {options.excludefilename}",
                  file=sys.stderr)
            sys.exit(1)
    else:
        options.toexclude = []

    # resolve args to module lists
    expanded = []
    for arg in args:
        if arg == '-':
            expanded.append(arg)
        else:
            expanded.extend(getFilesForName(arg))
    args = expanded

    # slurp through all the files
    visitor = GettextVisitor(options)
    for filename in args:
        if filename == '-':
            if options.verbose:
                print('Reading standard input')
            source = sys.stdin.buffer.read()
        else:
            if options.verbose:
                print(f'Working on {filename}')
            with open(filename, 'rb') as fp:
                source = fp.read()

        visitor.visit_file(source, filename)

    # write the output
    if options.outfile == '-':
        fp = sys.stdout
        closep = 0
    else:
        if options.outpath:
            options.outfile = os.path.join(options.outpath, options.outfile)
        fp = open(options.outfile, 'w')
        closep = 1
    try:
        write_pot_file(visitor.messages, options, fp)
    finally:
        if closep:
            fp.close()