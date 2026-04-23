def run_tests(argv=None):
    parse_cmd_line_args()
    if argv is None:
        argv = UNITTEST_ARGS

    # import test files.
    if SLOW_TESTS_FILE:
        if os.path.exists(SLOW_TESTS_FILE):
            with open(SLOW_TESTS_FILE) as fp:
                global slow_tests_dict
                slow_tests_dict = json.load(fp)
                # use env vars so pytest-xdist subprocesses can still access them
                os.environ['SLOW_TESTS_FILE'] = SLOW_TESTS_FILE
        else:
            warnings.warn(f'slow test file provided but not found: {SLOW_TESTS_FILE}', stacklevel=2)
    if DISABLED_TESTS_FILE:
        if os.path.exists(DISABLED_TESTS_FILE):
            with open(DISABLED_TESTS_FILE) as fp:
                global disabled_tests_dict
                disabled_tests_dict = json.load(fp)
                os.environ['DISABLED_TESTS_FILE'] = DISABLED_TESTS_FILE
        else:
            warnings.warn(f'disabled test file provided but not found: {DISABLED_TESTS_FILE}', stacklevel=2)
    # Determine the test launch mechanism
    if TEST_DISCOVER:
        _print_test_names()
        return

    # Before running the tests, lint to check that every test class extends from TestCase
    suite = unittest.TestLoader().loadTestsFromModule(__main__)
    if not lint_test_case_extension(suite):
        sys.exit(1)

    if SHOWLOCALS:
        argv = [
            argv[0],
            *(["--showlocals", "--tb=long", "--color=yes"] if USE_PYTEST else ["--locals"]),
            *argv[1:],
        ]

    if TEST_IN_SUBPROCESS:
        other_args = []
        if DISABLED_TESTS_FILE:
            other_args.append("--import-disabled-tests")
        if SLOW_TESTS_FILE:
            other_args.append("--import-slow-tests")
        if USE_PYTEST:
            other_args.append("--use-pytest")
        if RERUN_DISABLED_TESTS:
            other_args.append("--rerun-disabled-tests")
        if TEST_SAVE_XML:
            other_args += ['--save-xml', TEST_SAVE_XML]

        test_cases = (
            get_pytest_test_cases(argv) if USE_PYTEST else
            [case.id().split('.', 1)[1] for case in discover_test_cases_recursively(suite)]
        )

        failed_tests = []

        for test_case_full_name in test_cases:

            cmd = (
                [sys.executable] + [argv[0]] + other_args + argv[1:] +
                (["--pytest-single-test"] if USE_PYTEST else []) +
                [test_case_full_name]
            )
            string_cmd = " ".join(cmd)

            timeout = None if RERUN_DISABLED_TESTS else 15 * 60

            exitcode, _ = retry_shell(cmd, timeout=timeout, retries=0 if RERUN_DISABLED_TESTS else 1)

            if exitcode != 0:
                # This is sort of hacky, but add on relevant env variables for distributed tests.
                if 'TestDistBackendWithSpawn' in test_case_full_name:
                    backend = os.environ.get("BACKEND", "")
                    world_size = os.environ.get("WORLD_SIZE", "")
                    env_prefix = f"BACKEND={backend} WORLD_SIZE={world_size}"
                    string_cmd = env_prefix + " " + string_cmd
                # Log the command to reproduce the failure.
                print(f"Test exited with non-zero exitcode {exitcode}. Command to reproduce: {string_cmd}")
                failed_tests.append(test_case_full_name)

        if len(failed_tests) != 0:
            raise AssertionError(
                "{} unit test(s) failed:\n\t{}".format(
                    len(failed_tests), '\n\t'.join(failed_tests)
                )
            )

    elif RUN_PARALLEL > 1:
        test_cases = discover_test_cases_recursively(suite)
        test_batches = chunk_list(get_test_names(test_cases), RUN_PARALLEL)
        processes = []
        for i in range(RUN_PARALLEL):
            command = [sys.executable] + argv + [f'--log-suffix=-shard-{i + 1}'] + test_batches[i]
            processes.append(subprocess.Popen(command, universal_newlines=True))
        failed = False
        for p in processes:
            failed |= wait_for_process(p) != 0
        if failed:
            raise AssertionError("Some test shards have failed")
    elif USE_PYTEST:
        pytest_args = argv + ["--use-main-module"]
        test_report_path = ""
        if TEST_SAVE_XML:
            test_report_path = get_report_path(pytest=True)
            print(f'Test results will be stored in {test_report_path}')
            pytest_args.append(f'--junit-xml-reruns={test_report_path}')
        if PYTEST_SINGLE_TEST:
            pytest_args = PYTEST_SINGLE_TEST + pytest_args[1:]

        import pytest
        os.environ["NO_COLOR"] = "1"
        exit_code = pytest.main(args=pytest_args)
        if TEST_SAVE_XML:
            sanitize_pytest_xml(test_report_path)

        # exitcode of 5 means no tests were found, which happens since some test configs don't
        # run tests from certain files
        sys.exit(0 if exit_code == 5 else exit_code)
    elif TEST_SAVE_XML:
        # import here so that non-CI doesn't need xmlrunner installed
        import xmlrunner  # type: ignore[import]
        from xmlrunner.result import _XMLTestResult  # type: ignore[import]

        class XMLTestResultVerbose(_XMLTestResult):
            """
            Adding verbosity to test outputs:
            by default test summary prints 'skip',
            but we want to also print the skip reason.
            GH issue: https://github.com/pytorch/pytorch/issues/69014

            This works with unittest_xml_reporting<=3.2.0,>=2.0.0
            (3.2.0 is latest at the moment)
            """

            def addSkip(self, test, reason):
                super().addSkip(test, reason)
                for c in self.callback.__closure__:
                    if isinstance(c.cell_contents, str) and c.cell_contents == 'skip':
                        # this message is printed in test summary;
                        # it stands for `verbose_str` captured in the closure
                        c.cell_contents = f"skip: {reason}"

            def printErrors(self) -> None:
                super().printErrors()
                self.printErrorList("XPASS", self.unexpectedSuccesses)
        test_report_path = get_report_path()
        verbose = '--verbose' in argv or '-v' in argv
        if verbose:
            print(f'Test results will be stored in {test_report_path}')
        unittest.main(argv=argv, testRunner=xmlrunner.XMLTestRunner(
            output=test_report_path,
            verbosity=2 if verbose else 1,
            resultclass=XMLTestResultVerbose))
    elif REPEAT_COUNT > 1:
        for _ in range(REPEAT_COUNT):
            if not unittest.main(exit=False, argv=argv).result.wasSuccessful():
                sys.exit(-1)
    else:
        unittest.main(argv=argv)