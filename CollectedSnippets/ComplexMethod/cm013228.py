def parse_cmd_line_args():
    global DISABLED_TESTS_FILE
    global GRAPH_EXECUTOR
    global LOG_SUFFIX
    global PYTEST_SINGLE_TEST
    global REPEAT_COUNT
    global RERUN_DISABLED_TESTS
    global RUN_PARALLEL
    global SHOWLOCALS
    global SLOW_TESTS_FILE
    global TEST_BAILOUTS
    global TEST_DISCOVER
    global TEST_IN_SUBPROCESS
    global TEST_SAVE_XML
    global UNITTEST_ARGS
    global USE_PYTEST

    is_running_via_run_test = "run_test.py" in getattr(__main__, "__file__", "")
    parser = argparse.ArgumentParser(add_help=not is_running_via_run_test, allow_abbrev=False)
    parser.add_argument('--subprocess', action='store_true',
                        help='whether to run each test in a subprocess')
    parser.add_argument('--accept', action='store_true')
    parser.add_argument('--jit-executor', '--jit_executor', type=str)
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--test-bailouts', '--test_bailouts', action='store_true')
    parser.add_argument('--use-pytest', action='store_true')
    parser.add_argument('--save-xml', nargs='?', type=str,
                        const=_get_test_report_path(),
                        default=_get_test_report_path() if IS_CI else None)
    parser.add_argument('--discover-tests', action='store_true')
    parser.add_argument('--log-suffix', type=str, default="")
    parser.add_argument('--run-parallel', type=int, default=1)
    parser.add_argument('--import-slow-tests', type=str, nargs='?', const=DEFAULT_SLOW_TESTS_FILE)
    parser.add_argument('--import-disabled-tests', type=str, nargs='?', const=DEFAULT_DISABLED_TESTS_FILE)
    parser.add_argument('--rerun-disabled-tests', action='store_true')
    parser.add_argument('--pytest-single-test', type=str, nargs=1)
    parser.add_argument('--showlocals', action=argparse.BooleanOptionalAction, default=False)

# Only run when -h or --help flag is active to display both unittest and parser help messages.
    def run_unittest_help(argv):
        unittest.main(argv=argv)

    if '-h' in sys.argv or '--help' in sys.argv:
        help_thread = threading.Thread(target=run_unittest_help, args=(sys.argv,))
        help_thread.start()
        help_thread.join()

    args, remaining = parser.parse_known_args()
    if args.jit_executor == 'legacy':
        GRAPH_EXECUTOR = ProfilingMode.LEGACY
    elif args.jit_executor == 'profiling':
        GRAPH_EXECUTOR = ProfilingMode.PROFILING
    elif args.jit_executor == 'simple':
        GRAPH_EXECUTOR = ProfilingMode.SIMPLE
    else:
        # infer flags based on the default settings
        GRAPH_EXECUTOR = cppProfilingFlagsToProfilingMode()

    RERUN_DISABLED_TESTS = args.rerun_disabled_tests

    SLOW_TESTS_FILE = args.import_slow_tests
    DISABLED_TESTS_FILE = args.import_disabled_tests
    LOG_SUFFIX = args.log_suffix
    RUN_PARALLEL = args.run_parallel
    TEST_BAILOUTS = args.test_bailouts
    USE_PYTEST = args.use_pytest
    PYTEST_SINGLE_TEST = args.pytest_single_test
    TEST_DISCOVER = args.discover_tests
    TEST_IN_SUBPROCESS = args.subprocess
    TEST_SAVE_XML = args.save_xml
    REPEAT_COUNT = args.repeat
    SHOWLOCALS = args.showlocals
    if not getattr(expecttest, "ACCEPT", False):
        expecttest.ACCEPT = args.accept
    UNITTEST_ARGS = [sys.argv[0]] + remaining

    set_rng_seed()