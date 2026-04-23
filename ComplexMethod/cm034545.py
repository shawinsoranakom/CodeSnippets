def main() -> None:
    tests = find_tests()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test',
        metavar='TEST',
        dest='test_names',
        action='append',
        choices=[test.name for test in tests],
        help='test requirements to update'
    )

    parser.add_argument(
        '--pre-build-only',
        action='store_true',
        help='apply pre-build instructions to existing requirements',
    )

    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    test_names: set[str] = set(args.test_names or [])

    tests = [test for test in tests if test.name in test_names] if test_names else tests

    for test in tests:
        print(f'===[ {test.name} ]===', flush=True)

        if args.pre_build_only:
            test.update_pre_build()
        else:
            test.freeze_requirements()