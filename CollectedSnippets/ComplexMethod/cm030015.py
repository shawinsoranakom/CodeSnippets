def main():
    import argparse

    description = 'A simple command-line interface for tarfile module.'
    parser = argparse.ArgumentParser(description=description, color=True)
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Verbose output')
    parser.add_argument('--filter', metavar='<filtername>',
                        choices=_NAMED_FILTERS,
                        help='Filter for extraction')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-l', '--list', metavar='<tarfile>',
                       help='Show listing of a tarfile')
    group.add_argument('-e', '--extract', nargs='+',
                       metavar=('<tarfile>', '<output_dir>'),
                       help='Extract tarfile into target dir')
    group.add_argument('-c', '--create', nargs='+',
                       metavar=('<name>', '<file>'),
                       help='Create tarfile from sources')
    group.add_argument('-t', '--test', metavar='<tarfile>',
                       help='Test if a tarfile is valid')

    args = parser.parse_args()

    if args.filter and args.extract is None:
        parser.exit(1, '--filter is only valid for extraction\n')

    if args.test is not None:
        src = args.test
        if is_tarfile(src):
            with open(src, 'r') as tar:
                tar.getmembers()
                print(tar.getmembers(), file=sys.stderr)
            if args.verbose:
                print('{!r} is a tar archive.'.format(src))
        else:
            parser.exit(1, '{!r} is not a tar archive.\n'.format(src))

    elif args.list is not None:
        src = args.list
        if is_tarfile(src):
            with TarFile.open(src, 'r:*') as tf:
                tf.list(verbose=args.verbose)
        else:
            parser.exit(1, '{!r} is not a tar archive.\n'.format(src))

    elif args.extract is not None:
        if len(args.extract) == 1:
            src = args.extract[0]
            curdir = os.curdir
        elif len(args.extract) == 2:
            src, curdir = args.extract
        else:
            parser.exit(1, parser.format_help())

        if is_tarfile(src):
            with TarFile.open(src, 'r:*') as tf:
                tf.extractall(path=curdir, filter=args.filter)
            if args.verbose:
                if curdir == '.':
                    msg = '{!r} file is extracted.'.format(src)
                else:
                    msg = ('{!r} file is extracted '
                           'into {!r} directory.').format(src, curdir)
                print(msg)
        else:
            parser.exit(1, '{!r} is not a tar archive.\n'.format(src))

    elif args.create is not None:
        tar_name = args.create.pop(0)
        _, ext = os.path.splitext(tar_name)
        compressions = {
            # gz
            '.gz': 'gz',
            '.tgz': 'gz',
            # xz
            '.xz': 'xz',
            '.txz': 'xz',
            # bz2
            '.bz2': 'bz2',
            '.tbz': 'bz2',
            '.tbz2': 'bz2',
            '.tb2': 'bz2',
            # zstd
            '.zst': 'zst',
            '.tzst': 'zst',
        }
        tar_mode = 'w:' + compressions[ext] if ext in compressions else 'w'
        tar_files = args.create

        with TarFile.open(tar_name, tar_mode) as tf:
            for file_name in tar_files:
                tf.add(file_name)

        if args.verbose:
            print('{!r} file created.'.format(tar_name))