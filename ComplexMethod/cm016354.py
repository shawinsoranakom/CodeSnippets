def process_report(
    report: Path,
) -> dict[str, dict[str, int]]:
    """
    Return a list of disabled tests that should be re-enabled and those that are still
    flaky (failed or skipped)
    """
    root = ET.parse(report)

    # All rerun tests from a report are grouped here:
    #
    # * Success test should be re-enable if it's green after rerunning in all platforms
    #   where it is currently disabled
    # * Failures from pytest because pytest-flakefinder is used to run the same test
    #   multiple times, some could fails
    # * Skipped tests from unittest
    #
    # We want to keep track of how many times the test fails (num_red) or passes (num_green)
    all_tests: dict[str, dict[str, int]] = {}

    for test_case in root.iter(TESTCASE_TAG):
        # Parse the test case as string values only.
        parsed_test_case = process_xml_element(test_case, output_numbers=False)

        # Under --rerun-disabled-tests mode, a test is skipped when:
        # * it's skipped explicitly inside PyTorch code
        # * it's skipped because it's a normal enabled test
        # * or it's falky (num_red > 0 and num_green > 0)
        # * or it's failing (num_red > 0 and num_green == 0)
        #
        # We care only about the latter two here
        skipped = parsed_test_case.get("skipped", None)

        # NB: Regular ONNX tests could return a list of subskips here where each item in the
        # list is a skipped message.  In the context of rerunning disabled tests, we could
        # ignore this case as returning a list of subskips only happens when tests are run
        # normally
        if skipped and (
            type(skipped) is list or "num_red" not in skipped.get("message", "")
        ):
            continue

        name = parsed_test_case.get("name", "")
        classname = parsed_test_case.get("classname", "")
        filename = parsed_test_case.get("file", "")

        if not name or not classname or not filename:
            continue

        # Check if the test is a failure
        failure = parsed_test_case.get("failure", None)

        disabled_test_id = SEPARATOR.join([name, classname, filename])
        if disabled_test_id not in all_tests:
            all_tests[disabled_test_id] = {
                "num_green": 0,
                "num_red": 0,
            }

        # Under --rerun-disabled-tests mode, if a test is not skipped or failed, it's
        # counted as a success. Otherwise, it's still flaky or failing
        if skipped:
            try:
                stats = json.loads(skipped.get("message", ""))
            except json.JSONDecodeError:
                stats = {}

            all_tests[disabled_test_id]["num_green"] += stats.get("num_green", 0)
            all_tests[disabled_test_id]["num_red"] += stats.get("num_red", 0)
        elif failure:
            # As a failure, increase the failure count
            all_tests[disabled_test_id]["num_red"] += 1
        else:
            all_tests[disabled_test_id]["num_green"] += 1

    return all_tests