def patch_file(
    filename, test_dir, unexpected_successes, new_xfails, new_skips, unexpected_skips
):
    failures_directory = os.path.join(test_dir, "dynamo_expected_failures")
    skips_directory = os.path.join(test_dir, "dynamo_skips")

    dynamo_expected_failures = set(os.listdir(failures_directory))
    dynamo_skips = set(os.listdir(skips_directory))

    # These are hand written skips
    extra_dynamo_skips = set()
    with open(filename) as f:
        start = False
        for text in f.readlines():
            text = text.strip()
            if start:
                if text == "}":
                    break
                extra_dynamo_skips.add(text.strip(',"'))
            else:
                if text == "extra_dynamo_skips = {":
                    start = True

    def format(testcase):
        classname = testcase.attrib["classname"]
        name = testcase.attrib["name"]
        return f"{classname}.{name}"

    formatted_unexpected_successes = {
        f"{format(test)}" for test in unexpected_successes.values()
    }
    formatted_unexpected_skips = {
        f"{format(test)}" for test in unexpected_skips.values()
    }
    formatted_new_xfails = [f"{format(test)}" for test in new_xfails.values()]
    formatted_new_skips = [f"{format(test)}" for test in new_skips.values()]

    def remove_file(path, name):
        file = os.path.join(path, name)
        cmd = ["git", "rm", file]
        subprocess.run(cmd)

    def add_file(path, name):
        file = os.path.join(path, name)
        with open(file, "w") as fp:
            pass
        cmd = ["git", "add", file]
        subprocess.run(cmd)

    covered_unexpected_successes = set()

    # dynamo_expected_failures
    for test in dynamo_expected_failures:
        if test in formatted_unexpected_successes:
            covered_unexpected_successes.add(test)
            remove_file(failures_directory, test)
    for test in formatted_new_xfails:
        add_file(failures_directory, test)

    leftover_unexpected_successes = (
        formatted_unexpected_successes - covered_unexpected_successes
    )
    if len(leftover_unexpected_successes) > 0:
        print(
            "WARNING: we were unable to remove these "
            f"{len(leftover_unexpected_successes)} expectedFailures:"
        )
        for stuff in leftover_unexpected_successes:
            print(stuff)

    # dynamo_skips
    for test in dynamo_skips:
        if test in formatted_unexpected_skips:
            remove_file(skips_directory, test)
    for test in extra_dynamo_skips:
        if test in formatted_unexpected_skips:
            print(
                f"WARNING: {test} in dynamo_test_failures.py needs to be removed manually"
            )
    for test in formatted_new_skips:
        add_file(skips_directory, test)