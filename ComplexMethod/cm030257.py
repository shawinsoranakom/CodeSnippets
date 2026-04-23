def _test():
    import getopt
    inplace = False
    backup = False
    opts, args = getopt.getopt(sys.argv[1:], "ib:")
    for o, a in opts:
        if o == '-i': inplace = True
        if o == '-b': backup = a
    for line in input(args, inplace=inplace, backup=backup):
        if line[-1:] == '\n': line = line[:-1]
        if line[-1:] == '\r': line = line[:-1]
        print("%d: %s[%d]%s %s" % (lineno(), filename(), filelineno(),
                                   isfirstline() and "*" or "", line))
    print("%d: %s[%d]" % (lineno(), filename(), filelineno()))