def main():
    check_pip_packages()

    options = parse_args()
    tests_to_include_env = os.environ.get("TESTS_TO_INCLUDE", "").strip()
    if tests_to_include_env:
        # Parse env var tests to module names (strips .py suffix and ::method)
        env_tests = {parse_test_module(t) for t in tests_to_include_env.split()}

        if options.include != TESTS:
            # --include was explicitly provided, intersect with env var
            cli_tests = {parse_test_module(t) for t in options.include}
            options.include = list(env_tests & cli_tests)
        else:
            # No explicit --include, use env var tests
            options.include = list(env_tests)

        options.enable_td = False

    # Include sharding info in all metrics
    which_shard, num_shards = get_sharding_opts(options)
    add_global_metric("shard", which_shard)
    add_global_metric("num_shards", num_shards)

    test_directory = str(REPO_ROOT / "test")
    selected_tests = get_selected_tests(options)

    test_prioritizations = import_results()
    if len(test_prioritizations.get_all_tests()) == 0:
        options.enable_td = False
    test_prioritizations.amend_tests(selected_tests)

    os.makedirs(REPO_ROOT / "test" / "test-reports", exist_ok=True)

    if options.coverage and not PYTORCH_COLLECT_COVERAGE:
        shell(["coverage", "erase"])

    if IS_CI:
        # downloading test cases configuration to local environment
        get_test_case_configs(dirpath=test_directory)

    test_file_times_dict = load_test_file_times()
    test_class_times_dict = load_test_class_times()

    class TestBatch:
        """Defines a set of tests with similar priority that should be run together on the current shard"""

        name: str
        sharded_tests: list[ShardedTest]
        failures: list[TestFailure]

        def __init__(
            self, name: str, raw_tests: Sequence[TestRun], should_sort_shard: bool
        ):
            self.name = name
            self.failures = []
            self.time, self.sharded_tests = do_sharding(
                options,
                raw_tests,
                test_file_times_dict,
                test_class_times_dict,
                sort_by_time=should_sort_shard,
            )

        def __str__(self):
            s = f"Name: {self.name} (est. time: {round(self.time / 60, 2)}min)\n"
            serial = [test for test in self.sharded_tests if must_serial(test)]
            parallel = [test for test in self.sharded_tests if not must_serial(test)]
            s += f"  Serial tests ({len(serial)}):\n"
            s += "".join(f"    {test}\n" for test in serial)
            s += f"  Parallel tests ({len(parallel)}):\n"
            s += "".join(f"    {test}\n" for test in parallel)
            return s.strip()

    percent_to_run = 25 if options.enable_td else 100
    print_to_stderr(
        f"Running {percent_to_run}% of tests based on TD"
        if options.enable_td
        else "Running all tests"
    )
    include, exclude = test_prioritizations.get_top_per_tests(percent_to_run)

    test_batch = TestBatch("tests to run", include, False)
    test_batch_exclude = TestBatch("excluded", exclude, True)
    if IS_CI:
        gen_ci_artifact([x.to_json() for x in include], [x.to_json() for x in exclude])

    print_to_stderr(f"Running parallel tests on {NUM_PROCS} processes")
    print_to_stderr(test_batch)
    print_to_stderr(test_batch_exclude)

    if options.dry_run:
        return

    if options.dynamo:
        os.environ["PYTORCH_TEST_WITH_DYNAMO"] = "1"

    elif options.inductor:
        os.environ["PYTORCH_TEST_WITH_INDUCTOR"] = "1"

    if not options.no_translation_validation:
        os.environ["PYTORCH_TEST_WITH_TV"] = "1"

    try:
        # Actually run the tests
        start_time = time.time()
        run_tests(
            test_batch.sharded_tests, test_directory, options, test_batch.failures
        )
        elapsed_time = time.time() - start_time
        print_to_stderr(
            f"Running test batch '{test_batch.name}' cost {round(elapsed_time, 2)} seconds"
        )

    finally:
        if options.coverage:
            from coverage import Coverage

            with set_cwd(test_directory):
                cov = Coverage()
                if PYTORCH_COLLECT_COVERAGE:
                    cov.load()
                cov.combine(strict=False)
                cov.save()
                if not PYTORCH_COLLECT_COVERAGE:
                    cov.html_report()

        all_failures = test_batch.failures

        if IS_CI:
            for test, _ in all_failures:
                test_stats = test_prioritizations.get_test_stats(test)
                print_to_stderr("Emitting td_test_failure_stats_v2")
                emit_metric(
                    "td_test_failure_stats_v2",
                    {
                        "selected_tests": selected_tests,
                        "failure": str(test),
                        **test_stats,
                    },
                )
            gen_additional_test_failures_file(
                [test.test_file for test, _ in all_failures]
            )

    if len(all_failures):
        for _, err in all_failures:
            print_to_stderr(err)

        # A disabled test is expected to fail, so there is no need to report a failure here
        if not RERUN_DISABLED_TESTS:
            sys.exit(1)