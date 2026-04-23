def _main(args=None):
    import argparse
    parser = argparse.ArgumentParser(
        description='disassemble one or more pickle files',
        color=True,
    )
    parser.add_argument(
        'pickle_file',
        nargs='+', help='the pickle file')
    parser.add_argument(
        '-o', '--output',
        help='the file where the output should be written')
    parser.add_argument(
        '-m', '--memo', action='store_true',
        help='preserve memo between disassemblies')
    parser.add_argument(
        '-l', '--indentlevel', default=4, type=int,
        help='the number of blanks by which to indent a new MARK level')
    parser.add_argument(
        '-a', '--annotate',  action='store_true',
        help='annotate each line with a short opcode description')
    parser.add_argument(
        '-p', '--preamble', default="==> {name} <==",
        help='if more than one pickle file is specified, print this before'
        ' each disassembly')
    args = parser.parse_args(args)
    annotate = 30 if args.annotate else 0
    memo = {} if args.memo else None
    if args.output is None:
        output = sys.stdout
    else:
        output = open(args.output, 'w')
    try:
        for arg in args.pickle_file:
            if len(args.pickle_file) > 1:
                name = '<stdin>' if arg == '-' else arg
                preamble = args.preamble.format(name=name)
                output.write(preamble + '\n')
            if arg == '-':
                dis(sys.stdin.buffer, output, memo, args.indentlevel, annotate)
            else:
                with open(arg, 'rb') as f:
                    dis(f, output, memo, args.indentlevel, annotate)
    finally:
        if output is not sys.stdout:
            output.close()