def run_tests(
    selected_tests: list[ShardedTest],
    test_directory: str,
    options,
    failures: list[TestFailure],
) -> None:
    if len(selected_tests) == 0:
        return

    # parallel = in parallel with other files
    # serial = this file on it's own.  The file might still be run in parallel with itself (ex test_ops)
    selected_tests_parallel = [x for x in selected_tests if not must_serial(x)]
    selected_tests_serial = [
        x for x in selected_tests if x not in selected_tests_parallel
    ]

    # NB: This is a hack to make conftest.py and files it depends on available
    # on CPP_TESTS_DIR. We should see if the file could be turned into a
    # full-fledge ptest plugin instead
    conftest_files = [
        "conftest.py",
        "pytest_shard_custom.py",
    ]
    for conftest_file in conftest_files:
        cpp_file = os.path.join(CPP_TESTS_DIR, conftest_file)
        if (
            options.cpp
            and os.path.exists(CPP_TESTS_DIR)
            and os.path.isdir(CPP_TESTS_DIR)
            and not os.path.exists(cpp_file)
        ):
            shutil.copy(os.path.join(test_directory, conftest_file), cpp_file)

    def handle_complete(failure: TestFailure | None):
        failed = failure is not None
        if IS_CI and options.upload_artifacts_while_running:
            parse_xml_and_upload_json()
            zip_and_upload_artifacts(failed)
        if not failed:
            return False
        failures.append(failure)
        print_to_stderr(failure.message)
        return True

    keep_going_message = (
        "\n\nTip: You can keep running tests even on failure by passing --keep-going to run_test.py.\n"
        "If running on CI, add the 'keep-going' label to your PR and rerun your jobs."
    )

    pool = None
    try:
        for test in selected_tests_serial:
            options_clone = copy.deepcopy(options)
            if can_run_in_pytest(test):
                options_clone.pytest = True
            failure = run_test_module(test, test_directory, options_clone)
            test_failed = handle_complete(failure)
            if (
                test_failed
                and not options.continue_through_error
                and not RERUN_DISABLED_TESTS
            ):
                raise RuntimeError(failure.message + keep_going_message)

        # Run tests marked as serial first
        for test in selected_tests_parallel:
            options_clone = copy.deepcopy(options)
            if can_run_in_pytest(test):
                options_clone.pytest = True
            options_clone.additional_args.extend(["-m", "serial"])
            failure = run_test_module(test, test_directory, options_clone)
            test_failed = handle_complete(failure)
            if (
                test_failed
                and not options.continue_through_error
                and not RERUN_DISABLED_TESTS
            ):
                raise RuntimeError(failure.message + keep_going_message)

        # This is used later to constrain memory per proc on the GPU. On ROCm
        # the number of procs is the number of GPUs, so we don't need to do this
        os.environ["NUM_PARALLEL_PROCS"] = str(1 if torch.version.hip else NUM_PROCS)

        # See Note [ROCm parallel CI testing]
        pool = get_context("spawn").Pool(
            NUM_PROCS, maxtasksperchild=None if torch.version.hip else 1
        )

        def parallel_test_completion_callback(failure):
            test_failed = handle_complete(failure)
            if (
                test_failed
                and not options.continue_through_error
                and not RERUN_DISABLED_TESTS
            ):
                pool.terminate()

        for test in selected_tests_parallel:
            options_clone = copy.deepcopy(options)
            if can_run_in_pytest(test):
                options_clone.pytest = True
            options_clone.additional_args.extend(["-m", "not serial"])
            pool.apply_async(
                run_test_module,
                args=(test, test_directory, options_clone),
                callback=parallel_test_completion_callback,
            )
        pool.close()
        pool.join()
        del os.environ["NUM_PARALLEL_PROCS"]

    finally:
        if pool:
            pool.terminate()
            pool.join()

    return