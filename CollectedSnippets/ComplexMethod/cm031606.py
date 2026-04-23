def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='print out more information',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    collect = subparsers.add_parser(
        'collect', help='collect IDs from a set of HTML files'
    )
    collect.add_argument(
        'htmldir', type=Path, help='directory with HTML documentation'
    )
    collect.add_argument(
        '-o',
        '--outfile',
        help='File to save the result in; default <htmldir>/html-ids.json.gz',
    )

    check = subparsers.add_parser('check', help='check two archives of IDs')
    check.add_argument(
        'baseline_file', type=Path, help='file with baseline IDs'
    )
    check.add_argument('checked_file', type=Path, help='file with checked IDs')
    check.add_argument(
        '-x',
        '--exclude-file',
        type=Path,
        help='file with IDs to exclude from the check',
    )

    args = parser.parse_args(argv[1:])

    if args.verbose:
        verbose_print = functools.partial(print, file=sys.stderr)
    else:

        def verbose_print(*args, **kwargs):
            """do nothing"""

    if args.command == 'collect':
        ids = gather_ids(args.htmldir, verbose_print=verbose_print)
        if args.outfile is None:
            args.outfile = args.htmldir / 'html-ids.json.gz'
        with gzip.open(args.outfile, 'wt', encoding='utf-8') as zfile:
            json.dump({'ids_by_page': ids}, zfile)

    if args.command == 'check':
        with gzip.open(args.baseline_file) as zfile:
            baseline = json.load(zfile)['ids_by_page']
        with gzip.open(args.checked_file) as zfile:
            checked = json.load(zfile)['ids_by_page']
        excluded = set()
        if args.exclude_file:
            with open(args.exclude_file, encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        name, sep, excluded_id = line.partition(':')
                        if sep:
                            excluded.add((name.strip(), excluded_id.strip()))
        if do_check(baseline, checked, excluded, verbose_print=verbose_print):
            verbose_print('All OK')
        else:
            sys.stdout.flush()
            print(
                'ERROR: Removed IDs found',
                'The above HTML IDs were removed from the documentation, '
                + 'resulting in broken links. Please add them back.',
                sep='\n',
                file=sys.stderr,
            )
            if args.exclude_file:
                print(f'Alternatively, add them to {args.exclude_file}.')
            sys.exit(1)