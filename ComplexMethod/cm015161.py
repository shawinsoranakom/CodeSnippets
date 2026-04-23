def run_test(
    test_module: ShardedTest,
    test_directory,
    options,
    launcher_cmd=None,
    extra_unittest_args=None,
    env=None,
    print_log=True,
) -> int:
    scribe_token = os.getenv("SCRIBE_GRAPHQL_ACCESS_TOKEN", "")
    if scribe_token:
        print_to_stderr("SCRIBE_GRAPHQL_ACCESS_TOKEN is set")
    else:
        print_to_stderr("SCRIBE_GRAPHQL_ACCESS_TOKEN is NOT set")

    env = env or os.environ.copy()
    maybe_set_hip_visible_devies()
    unittest_args = options.additional_args.copy()
    test_file = test_module.name
    stepcurrent_key = test_file

    is_distributed_test = test_file.startswith(DISTRIBUTED_TEST_PREFIX)
    is_cpp_test = _is_cpp_test(test_file)
    # NB: Rerun disabled tests depends on pytest-flakefinder and it doesn't work with
    # pytest-cpp atm. We also don't have support to disable C++ test yet, so it's ok
    # to just return successfully here
    if is_cpp_test and RERUN_DISABLED_TESTS:
        print_to_stderr(
            "Skipping C++ tests when running under RERUN_DISABLED_TESTS mode"
        )
        return 0

    if is_cpp_test:
        stepcurrent_key = f"{test_file}_{os.urandom(8).hex()}"
    else:
        unittest_args.extend(
            [
                f"--shard-id={test_module.shard}",
                f"--num-shards={test_module.num_shards}",
            ]
        )
        stepcurrent_key = f"{test_file}_{test_module.shard}_{os.urandom(8).hex()}"

    if options.verbose:
        unittest_args.append(f"-{'v' * options.verbose}")  # in case of pytest

    if test_file in RUN_PARALLEL_BLOCKLIST:
        unittest_args = [
            arg for arg in unittest_args if not arg.startswith("--run-parallel")
        ]

    if extra_unittest_args:
        if not isinstance(extra_unittest_args, list):
            raise AssertionError(
                f"extra_unittest_args must be a list, got {type(extra_unittest_args)}"
            )
        unittest_args.extend(extra_unittest_args)

    # If using pytest, replace -f with equivalent -x
    if options.pytest:
        unittest_args.extend(
            get_pytest_args(
                options,
                is_cpp_test=is_cpp_test,
                is_distributed_test=is_distributed_test,
            )
        )
        unittest_args.extend(test_module.get_pytest_args())
        replacement = {"-f": "-x", "-dist=loadfile": "--dist=loadfile"}
        unittest_args = [replacement.get(arg, arg) for arg in unittest_args]

    if options.showlocals:
        if options.pytest:
            unittest_args.extend(["--showlocals", "--tb=long", "--color=yes"])
        else:
            unittest_args.append("--locals")

    # NB: These features are not available for C++ tests, but there is little incentive
    # to implement it because we have never seen a flaky C++ test before.
    if IS_CI and not is_cpp_test:
        ci_args = ["--import-slow-tests", "--import-disabled-tests"]
        if RERUN_DISABLED_TESTS:
            ci_args.append("--rerun-disabled-tests")
        # use the downloaded test cases configuration, not supported in pytest
        unittest_args.extend(ci_args)

    if test_file in PYTEST_SKIP_RETRIES:
        if not options.pytest:
            raise RuntimeError(
                "A test running without pytest cannot skip retries using "
                "the PYTEST_SKIP_RETRIES set."
            )
        unittest_args = [arg for arg in unittest_args if "--reruns" not in arg]

    # Extra arguments are not supported with pytest
    executable = get_executable_command(options, is_cpp_test=is_cpp_test)
    if not executable:
        # If there is no eligible executable returning here, it means an unsupported
        # case such as coverage for C++ test. So just returning ok makes sense
        return 0

    if is_cpp_test:
        # C++ tests are not the regular test directory
        if CPP_TESTS_DIR:
            cpp_test = os.path.join(
                CPP_TESTS_DIR,
                test_file.replace(f"{CPP_TEST_PREFIX}/", ""),
            )
        else:
            cpp_test = os.path.join(
                Path(test_directory).parent,
                CPP_TEST_PATH,
                test_file.replace(f"{CPP_TEST_PREFIX}/", ""),
            )

        argv = [
            cpp_test if sys.platform != "win32" else cpp_test + ".exe"
        ] + unittest_args
    else:
        # Can't call `python -m unittest test_*` here because it doesn't run code
        # in `if __name__ == '__main__': `. So call `python test_*.py` instead.
        argv = [test_file + ".py"] + unittest_args

    os.makedirs(REPO_ROOT / "test" / "test-reports", exist_ok=True)
    if options.pipe_logs:
        log_fd, log_path = tempfile.mkstemp(
            dir=REPO_ROOT / "test" / "test-reports",
            prefix=f"{sanitize_file_name(str(test_module))}_",
            suffix="_toprint.log",
        )
        os.close(log_fd)

    command = (launcher_cmd or []) + executable + argv
    should_retry = (
        "--subprocess" not in command
        and not RERUN_DISABLED_TESTS
        and not is_cpp_test
        and "-n" not in command
    )
    timeout = (
        None
        if not options.enable_timeout
        else THRESHOLD * 6
        if IS_SLOW
        else THRESHOLD * 3
        if should_retry
        and isinstance(test_module, ShardedTest)
        and test_module.time is not None
        else THRESHOLD * 3
        if is_cpp_test
        else None
    )
    print_to_stderr(f"Executing {command} ... [{datetime.now()}]")

    with ExitStack() as stack:
        output = None
        if options.pipe_logs:
            output = stack.enter_context(open(log_path, "w"))

        if should_retry:
            ret_code, was_rerun = run_test_retries(
                command,
                test_directory,
                env,
                timeout,
                stepcurrent_key,
                output,
                options.continue_through_error,
                test_file,
                options,
            )
        else:
            command.extend([f"--sc={stepcurrent_key}", "--print-items"])
            ret_code, was_rerun = retry_shell(
                command,
                test_directory,
                stdout=output,
                stderr=output,
                env=env,
                timeout=timeout,
                retries=0,
            )

            # Pytest return code 5 means no test is collected. Exit code 4 is
            # returned when the binary is not a C++ test executable, but 4 can
            # also be returned if the file fails before running any tests. All
            # binary files under build/bin that are not C++ test at the time of
            # this writing have been excluded and new ones should be added to
            # the list of exclusions in tools/testing/discover_tests.py
            ret_code = 0 if ret_code == 5 else ret_code

    if options.pipe_logs and print_log:
        handle_log_file(
            test_module, log_path, failed=(ret_code != 0), was_rerun=was_rerun
        )
    return ret_code