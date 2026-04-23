def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the PyTorch unit test suite",
        epilog="where TESTS is any of: {}".format(", ".join(TESTS)),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Print verbose information and test-by-test results",
    )
    parser.add_argument(
        "--showlocals",
        action=argparse.BooleanOptionalAction,
        default=strtobool(os.environ.get("TEST_SHOWLOCALS", "False")),
        help="Show local variables in tracebacks (default: True)",
    )
    parser.add_argument("--jit", "--jit", action="store_true", help="run all jit tests")
    parser.add_argument(
        "--distributed-tests",
        "--distributed-tests",
        action="store_true",
        help="Run all distributed tests",
    )
    parser.add_argument(
        "--include-cpython-tests",
        "--include-cpython-tests",
        action="store_true",
        help="If this flag is present, we will only run cpython tests.",
    )
    parser.add_argument(
        "--include-dynamo-core-tests",
        "--include-dynamo-core-tests",
        action="store_true",
        help=(
            "If this flag is present, we will only run dynamo tests. "
            "If this flag is not present, we will run all tests "
            "(including dynamo tests)."
        ),
    )
    parser.add_argument(
        "--include-inductor-core-tests",
        "--include-inductor-core-tests",
        action="store_true",
        help=(
            "If this flag is present, we will only run inductor tests. "
            "If this flag is not present, we will run all tests "
            "(including inductor tests)."
        ),
    )
    parser.add_argument(
        "--functorch",
        "--functorch",
        action="store_true",
        help=(
            "If this flag is present, we will only run functorch tests. "
            "If this flag is not present, we will run all tests "
            "(including functorch tests)."
        ),
    )
    parser.add_argument(
        "--einops",
        "--einops",
        action="store_true",
        help=(
            "If this flag is present, we will only run einops tests. "
            "If this flag is not present, we will run all tests "
            "(including einops tests)."
        ),
    )
    parser.add_argument(
        "--mps",
        "--mps",
        action="store_true",
        help=(
            "If this flag is present, we will only run subset of tests, such as test_mps, test_nn, ..."
        ),
    )
    parser.add_argument(
        "--xpu",
        "--xpu",
        action="store_true",
        help=("If this flag is present, we will run xpu tests except XPU_BLOCK_LIST"),
    )
    parser.add_argument(
        "--openreg",
        "--openreg",
        action="store_true",
        help=("If this flag is present, we will only run test_openreg"),
    )
    parser.add_argument(
        "--cpp",
        "--cpp",
        action="store_true",
        help=("If this flag is present, we will only run C++ tests"),
    )
    parser.add_argument(
        "-core",
        "--core",
        action="store_true",
        help="Only run core tests, or tests that validate PyTorch's ops, modules,"
        "and autograd. They are defined by CORE_TEST_LIST.",
    )
    parser.add_argument(
        "--onnx",
        "--onnx",
        action="store_true",
        help=(
            "Only run ONNX tests, or tests that validate PyTorch's ONNX export. "
            "If this flag is not present, we will exclude ONNX tests."
        ),
    )
    parser.add_argument(
        "-k",
        "--pytest-k-expr",
        default="",
        help="Pass to pytest as its -k expr argument",
    )
    parser.add_argument(
        "-c",
        "--coverage",
        action="store_true",
        help="enable coverage",
        default=PYTORCH_COLLECT_COVERAGE,
    )
    parser.add_argument(
        "-i",
        "--include",
        nargs="+",
        choices=TestChoices(TESTS),
        default=TESTS,
        metavar="TESTS",
        help="select a set of tests to include (defaults to ALL tests)."
        " tests must be a part of the TESTS list defined in run_test.py",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        nargs="+",
        choices=TESTS,
        metavar="TESTS",
        default=[],
        help="select a set of tests to exclude",
    )
    parser.add_argument(
        "--ignore-win-blocklist",
        action="store_true",
        help="always run blocklisted windows tests",
    )
    # NS: Disable target determination until it can be made more reliable
    # parser.add_argument(
    #     "--determine-from",
    #     help="File of affected source filenames to determine which tests to run.",
    # )
    parser.add_argument(
        "--continue-through-error",
        "--keep-going",
        action="store_true",
        help="Runs the full test suite despite one of the tests failing",
        default=strtobool(os.environ.get("CONTINUE_THROUGH_ERROR", "False")),
    )
    parser.add_argument(
        "--pipe-logs",
        action="store_true",
        help="Print logs to output file while running tests.  True if in CI and env var is not set",
        default=IS_CI and not strtobool(os.environ.get("VERBOSE_TEST_LOGS", "False")),
    )
    parser.add_argument(
        "--enable-timeout",
        action="store_true",
        help="Set a timeout based on the test times json file.  Only works if there are test times available",
        default=IS_CI and not strtobool(os.environ.get("NO_TEST_TIMEOUT", "False")),
    )
    GITHUB_WORKFLOW = os.environ.get("GITHUB_WORKFLOW", "slow")
    parser.add_argument(
        "--enable-td",
        action="store_true",
        help="Enables removing tests based on TD",
        default=IS_CI
        and get_pr_number() is not None
        and not strtobool(os.environ.get("NO_TD", "False"))
        and not IS_MACOS
        and "xpu" not in BUILD_ENVIRONMENT
        and "onnx" not in BUILD_ENVIRONMENT
        and (
            GITHUB_WORKFLOW in ("trunk", "pull")
            or GITHUB_WORKFLOW.startswith(("rocm-", "periodic-rocm-"))
        ),
    )
    parser.add_argument(
        "--shard",
        nargs=2,
        type=int,
        help="runs a shard of the tests (taking into account other selections), e.g., "
        "--shard 2 3 will break up the selected tests into 3 shards and run the tests "
        "in the 2nd shard (the first number should not exceed the second)",
    )
    parser.add_argument(
        "--exclude-jit-executor",
        action="store_true",
        help="exclude tests that are run for a specific jit config",
    )
    parser.add_argument(
        "--exclude-torch-export-tests",
        action="store_true",
        help="exclude torch export tests",
    )
    parser.add_argument(
        "--exclude-aot-dispatch-tests",
        action="store_true",
        help="exclude aot dispatch tests",
    )
    parser.add_argument(
        "--exclude-distributed-tests",
        action="store_true",
        help="exclude distributed tests",
    )
    parser.add_argument(
        "--exclude-inductor-tests",
        action="store_true",
        help="exclude inductor tests",
    )
    parser.add_argument(
        "--exclude-quantization-tests",
        action="store_true",
        help="exclude quantization tests",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list the test that will run.",
    )
    parser.add_argument(
        "--xdoctest-command",
        default="all",
        help=(
            "Control the specific doctest action. "
            "Use 'list' to simply parse doctests and check syntax. "
            "Use 'all' to execute all doctests or specify a specific "
            "doctest to run"
        ),
    )
    parser.add_argument(
        "--no-translation-validation",
        action="store_false",
        help="Run tests without translation validation.",
    )
    parser.add_argument(
        "--upload-artifacts-while-running",
        action="store_true",
        default=IS_CI,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dynamo",
        action="store_true",
        help="Run tests with TorchDynamo+EagerBackend turned on",
    )
    group.add_argument(
        "--inductor",
        action="store_true",
        help="Run tests with TorchInductor turned on",
    )

    args, extra = parser.parse_known_args()
    if "--" in extra:
        extra.remove("--")
    args.additional_args = extra
    return args