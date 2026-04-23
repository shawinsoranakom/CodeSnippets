def check(file):
    """check(file_or_dir)

    If file_or_dir is a directory and not a symbolic link, then recursively
    descend the directory tree named by file_or_dir, checking all .py files
    along the way. If file_or_dir is an ordinary Python source file, it is
    checked for whitespace related problems. The diagnostic messages are
    written to standard output using the print statement.
    """

    if os.path.isdir(file) and not os.path.islink(file):
        if verbose:
            print("%r: listing directory" % (file,))
        names = os.listdir(file)
        for name in names:
            fullname = os.path.join(file, name)
            if (os.path.isdir(fullname) and
                not os.path.islink(fullname) or
                os.path.normcase(name[-3:]) == ".py"):
                check(fullname)
        return

    try:
        f = tokenize.open(file)
    except OSError as msg:
        errprint("%r: I/O Error: %s" % (file, msg))
        return

    if verbose > 1:
        print("checking %r ..." % file)

    try:
        process_tokens(tokenize.generate_tokens(f.readline))

    except tokenize.TokenError as msg:
        errprint("%r: Token Error: %s" % (file, msg))
        return

    except IndentationError as msg:
        errprint("%r: Indentation Error: %s" % (file, msg))
        return

    except SyntaxError as msg:
        errprint("%r: Syntax Error: %s" % (file, msg))
        return

    except NannyNag as nag:
        badline = nag.get_lineno()
        line = nag.get_line()
        if verbose:
            print("%r: *** Line %d: trouble in tab city! ***" % (file, badline))
            print("offending line: %r" % (line,))
            print(nag.get_msg())
        else:
            if ' ' in file: file = '"' + file + '"'
            if filename_only: print(file)
            else: print(file, badline, repr(line))
        return

    finally:
        f.close()

    if verbose:
        print("%r: Clean bill of health." % (file,))