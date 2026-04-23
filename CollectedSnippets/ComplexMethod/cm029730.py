def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(description=
        "A simple command line interface for the gzip module: act like gzip, "
        "but do not delete the input file.",
        color=True,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--fast', action='store_true', help='compress faster')
    group.add_argument('--best', action='store_true', help='compress better')
    group.add_argument("-d", "--decompress", action="store_true",
                        help="act like gunzip instead of gzip")

    parser.add_argument("args", nargs="*", default=["-"], metavar='file')
    args = parser.parse_args()

    compresslevel = _COMPRESS_LEVEL_TRADEOFF
    if args.fast:
        compresslevel = _COMPRESS_LEVEL_FAST
    elif args.best:
        compresslevel = _COMPRESS_LEVEL_BEST

    for arg in args.args:
        if args.decompress:
            if arg == "-":
                f = GzipFile(filename="", mode="rb", fileobj=sys.stdin.buffer)
                g = sys.stdout.buffer
            else:
                if arg[-3:] != ".gz":
                    sys.exit(f"filename doesn't end in .gz: {arg!r}")
                f = open(arg, "rb")
                g = builtins.open(arg[:-3], "wb")
        else:
            if arg == "-":
                f = sys.stdin.buffer
                g = GzipFile(filename="", mode="wb", fileobj=sys.stdout.buffer,
                             compresslevel=compresslevel)
            else:
                f = builtins.open(arg, "rb")
                g = open(arg + ".gz", "wb")
        while True:
            chunk = f.read(READ_BUFFER_SIZE)
            if not chunk:
                break
            g.write(chunk)
        if g is not sys.stdout.buffer:
            g.close()
        if f is not sys.stdin.buffer:
            f.close()