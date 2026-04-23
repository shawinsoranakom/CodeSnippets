def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file", type=Path, metavar='FILE', nargs='?',
        default=DEFAULT_MANIFEST_PATH,
        help=f"file with the stable abi manifest (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--generate", action='store_true',
        help="generate file(s), rather than just checking them",
    )
    parser.add_argument(
        "--generate-all", action='store_true',
        help="as --generate, but generate all file(s) using default filenames."
             " (unlike --all, does not run any extra checks)",
    )
    parser.add_argument(
        "-a", "--all", action='store_true',
        help="run all available checks using default filenames",
    )
    parser.add_argument(
        "-l", "--list", action='store_true',
        help="list available generators and their default filenames; then exit",
    )
    parser.add_argument(
        "--dump", action='store_true',
        help="dump the manifest contents (used for debugging the parser)",
    )

    actions_group = parser.add_argument_group('actions')
    for gen in generators:
        actions_group.add_argument(
            gen.arg_name, dest=gen.var_name,
            type=str, nargs="?", default=MISSING,
            metavar='FILENAME',
            help=gen.__doc__,
        )
    actions_group.add_argument(
        '--unixy-check', action='store_true',
        help=do_unixy_check.__doc__,
    )
    args = parser.parse_args()

    base_path = args.file.parent.parent

    if args.list:
        for gen in generators:
            print(f'{gen.arg_name}: {(base_path / gen.default_path).resolve()}')
        sys.exit(0)

    run_all_generators = args.generate_all

    if args.generate_all:
        args.generate = True

    if args.all:
        run_all_generators = True
        if UNIXY:
            args.unixy_check = True

    try:
        file = args.file.open('rb')
    except FileNotFoundError as err:
        if args.file.suffix == '.txt':
            # Provide a better error message
            suggestion = args.file.with_suffix('.toml')
            raise FileNotFoundError(
                f'{args.file} not found. Did you mean {suggestion} ?') from err
        raise
    with file:
        manifest = parse_manifest(file)

    check_private_names(manifest)

    # Remember results of all actions (as booleans).
    # At the end we'll check that at least one action was run,
    # and also fail if any are false.
    results = {}

    if args.dump:
        for line in manifest.dump():
            print(line)
        results['dump'] = check_dump(manifest, args.file)

    for gen in generators:
        filename = getattr(args, gen.var_name)
        if filename is None or (run_all_generators and filename is MISSING):
            filename = base_path / gen.default_path
        elif filename is MISSING:
            continue

        results[gen.var_name] = generate_or_check(manifest, args, filename, gen)

    if args.unixy_check:
        results['unixy_check'] = do_unixy_check(manifest, args)

    if not results:
        if args.generate:
            parser.error('No file specified. Use --generate-all to regenerate '
                         'all files, or --help for usage.')
        parser.error('No check specified. Use --all to check all files, '
                     'or --help for usage.')

    failed_results = [name for name, result in results.items() if not result]

    if failed_results:
        raise Exception(f"""
        These checks related to the stable ABI did not succeed:
            {', '.join(failed_results)}

        If you see diffs in the output, files derived from the stable
        ABI manifest the were not regenerated.
        Run `make regen-limited-abi` to fix this.

        Otherwise, see the error(s) above.

        The stable ABI manifest is at: {args.file}
        Note that there is a process to follow when modifying it.

        You can read more about the limited API and its contracts at:

        https://docs.python.org/3/c-api/stable.html

        And in PEP 384:

        https://peps.python.org/pep-0384/
        """)