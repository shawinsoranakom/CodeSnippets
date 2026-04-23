def main():
    """Small main program"""
    import sys, getopt
    usage = f"""usage: {sys.argv[0]} [-h|-d|-e|-u] [file|-]
        -h: print this help message and exit
        -d, -u: decode
        -e: encode (default)"""
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hdeu')
    except getopt.error as msg:
        sys.stdout = sys.stderr
        print(msg)
        print(usage)
        sys.exit(2)
    func = encode
    for o, a in opts:
        if o == '-e': func = encode
        if o == '-d': func = decode
        if o == '-u': func = decode
        if o == '-h': print(usage); return
    if args and args[0] != '-':
        with open(args[0], 'rb') as f:
            func(f, sys.stdout.buffer)
    else:
        if sys.stdin.isatty():
            # gh-138775: read terminal input data all at once to detect EOF
            import io
            data = sys.stdin.buffer.read()
            buffer = io.BytesIO(data)
        else:
            buffer = sys.stdin.buffer
        func(buffer, sys.stdout.buffer)