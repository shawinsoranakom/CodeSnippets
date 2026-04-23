def cli():
    """Command-line interface (looks at sys.argv to decide what to do)."""
    import getopt
    class BadUsage(Exception): pass

    _adjust_cli_sys_path()

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'bk:n:p:w')
        writing = False
        start_server = False
        open_browser = False
        port = 0
        hostname = 'localhost'
        for opt, val in opts:
            if opt == '-b':
                start_server = True
                open_browser = True
            if opt == '-k':
                apropos(val)
                return
            if opt == '-p':
                start_server = True
                port = val
            if opt == '-w':
                writing = True
            if opt == '-n':
                start_server = True
                hostname = val

        if start_server:
            browse(port, hostname=hostname, open_browser=open_browser)
            return

        if not args: raise BadUsage
        for arg in args:
            if ispath(arg) and not os.path.exists(arg):
                print('file %r does not exist' % arg)
                sys.exit(1)
            try:
                if ispath(arg) and os.path.isfile(arg):
                    arg = importfile(arg)
                if writing:
                    if ispath(arg) and os.path.isdir(arg):
                        writedocs(arg)
                    else:
                        writedoc(arg)
                else:
                    help.help(arg, is_cli=True)
            except (ImportError, ErrorDuringImport) as value:
                print(value)
                sys.exit(1)

    except (getopt.error, BadUsage):
        cmd = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        print("""pydoc - the Python documentation tool

{cmd} <name> ...
    Show text documentation on something.  <name> may be the name of a
    Python keyword, topic, function, module, or package, or a dotted
    reference to a class or function within a module or module in a
    package.  If <name> contains a '{sep}', it is used as the path to a
    Python source file to document. If name is 'keywords', 'topics',
    or 'modules', a listing of these things is displayed.

{cmd} -k <keyword>
    Search for a keyword in the synopsis lines of all available modules.

{cmd} -n <hostname>
    Start an HTTP server with the given hostname (default: localhost).

{cmd} -p <port>
    Start an HTTP server on the given port on the local machine.  Port
    number 0 can be used to get an arbitrary unused port.

{cmd} -b
    Start an HTTP server on an arbitrary unused port and open a web browser
    to interactively browse documentation.  This option can be used in
    combination with -n and/or -p.

{cmd} -w <name> ...
    Write out the HTML documentation for a module to a file in the current
    directory.  If <name> contains a '{sep}', it is treated as a filename; if
    it names a directory, documentation is written for all the contents.
""".format(cmd=cmd, sep=os.sep))