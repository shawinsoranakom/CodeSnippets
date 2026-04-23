def main():
    import getopt
    global verbose, recurse, dryrun, makebackup, spec_newline
    try:
        opts, args = getopt.getopt(sys.argv[1:], "drnvh",
            ["dryrun", "recurse", "nobackup", "verbose", "newline=", "help"])
    except getopt.error as msg:
        usage(msg)
        return
    for o, a in opts:
        if o in ('-d', '--dryrun'):
            dryrun = True
        elif o in ('-r', '--recurse'):
            recurse = True
        elif o in ('-n', '--nobackup'):
            makebackup = False
        elif o in ('-v', '--verbose'):
            verbose = True
        elif o in ('--newline',):
            if not a.upper() in ('CRLF', 'LF'):
                usage()
                return
            spec_newline = dict(CRLF='\r\n', LF='\n')[a.upper()]
        elif o in ('-h', '--help'):
            usage()
            return
    if not args:
        r = Reindenter(sys.stdin)
        r.run()
        r.write(sys.stdout)
        return
    for arg in args:
        check(arg)