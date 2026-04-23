def run_test_retries(
    command,
    test_directory,
    env,
    timeout,
    stepcurrent_key,
    output,
    continue_through_error,
    test_file,
    options,
):
    # Run the test with -x to stop at first failure.  Rerun the test by itself.
    # If it succeeds, move on to the rest of the tests in a new process.  If it
    # still fails, see below
    #
    # If continue through error is not set, then we fail fast.
    #
    # If continue through error is set, then we skip that test, and keep going.
    # Basically if the same test fails 3 times in a row, skip the test on the
    # next run, but still fail in the end. I take advantage of the value saved
    # in stepcurrent to keep track of the most recently run test (which is the
    # one that failed if there was a failure).

    def print_to_file(s):
        print(s, file=output, flush=True)

    num_failures = defaultdict(int)

    def read_pytest_cache(key: str) -> Any:
        cache_file = (
            REPO_ROOT / ".pytest_cache/v/cache/stepcurrent" / stepcurrent_key / key
        )
        try:
            with open(cache_file) as f:
                return f.read()
        except FileNotFoundError:
            return None

    print_items = ["--print-items"]
    sc_command = f"--sc={stepcurrent_key}"
    while True:
        ret_code, _ = retry_shell(
            command + [sc_command] + print_items,
            test_directory,
            stdout=output,
            stderr=output,
            env=env,
            timeout=timeout,
            retries=0,  # no retries here, we do it ourselves, this is because it handles timeout exceptions well
        )
        ret_code = 0 if ret_code == 5 else ret_code
        if ret_code == 0 and not sc_command.startswith("--rs="):
            break  # Got to the end of the test suite successfully
        signal_name = f" ({SIGNALS_TO_NAMES_DICT[-ret_code]})" if ret_code < 0 else ""
        print_to_file(f"Got exit code {ret_code}{signal_name}")

        # Read what just failed/ran
        try:
            current_failure = read_pytest_cache("lastrun")
            if current_failure is None:
                raise FileNotFoundError
            if current_failure == "null":
                current_failure = f"'{test_file}'"
        except FileNotFoundError:
            print_to_file(
                "No stepcurrent file found. Either pytest didn't get to run (e.g. import error)"
                + " or file got deleted (contact dev infra)"
            )
            break

        env = try_set_cpp_stack_traces(env, command, set=False)
        if ret_code != 0:
            num_failures[current_failure] += 1

        if ret_code == 0:
            # Rerunning the previously failing test succeeded, so now we can
            # skip it and move on
            sc_command = f"--scs={stepcurrent_key}"
            print_to_file(
                "Test succeeded in new process, continuing with the rest of the tests"
            )
        elif num_failures[current_failure] >= 3:
            # This is for log classifier so it can prioritize consistently
            # failing tests instead of reruns. [1:-1] to remove quotes
            print_to_file(f"FAILED CONSISTENTLY: {current_failure[1:-1]}")
            if (
                read_pytest_cache("made_failing_xml") == "false"
                and IS_CI
                and options.upload_artifacts_while_running
            ):
                upload_adhoc_failure_json(test_file, current_failure[1:-1])

            if not continue_through_error:
                print_to_file("Stopping at first consistent failure")
                break
            sc_command = f"--scs={stepcurrent_key}"
            print_to_file(
                "Test failed consistently, "
                "continuing with the rest of the tests due to continue-through-error being set"
            )
        else:
            env = try_set_cpp_stack_traces(env, command, set=True)
            sc_command = f"--rs={stepcurrent_key}"
            print_to_file("Retrying single test...")
        print_items = []  # do not continue printing them, massive waste of space

    consistent_failures = [x[1:-1] for x in num_failures if num_failures[x] >= 3]
    flaky_failures = [x[1:-1] for x in num_failures if 0 < num_failures[x] < 3]
    if len(flaky_failures) > 0:
        print_to_file(
            "The following tests failed and then succeeded when run in a new process"
            + f"{flaky_failures}",
        )
    if len(consistent_failures) > 0:
        print_to_file(f"The following tests failed consistently: {consistent_failures}")
        return 1, True
    return ret_code, any(x > 0 for x in num_failures.values())