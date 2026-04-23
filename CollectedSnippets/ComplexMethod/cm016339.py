def should_run_test(
    target_det_list: list[str], test: str, touched_files: list[str], options: Any
) -> bool:
    test = parse_test_module(test)
    # Some tests are faster to execute than to determine.
    if test not in target_det_list:
        if options.verbose:
            print_to_stderr(f"Running {test} without determination")
        return True
    # HACK: "no_ninja" is not a real module
    if test.endswith("_no_ninja"):
        test = test[: (-1 * len("_no_ninja"))]
    if test.endswith("_ninja"):
        test = test[: (-1 * len("_ninja"))]

    dep_modules = get_dep_modules(test)

    for touched_file in touched_files:
        file_type = test_impact_of_file(touched_file)
        if file_type == "NONE":
            continue
        elif file_type == "CI":
            # Force all tests to run if any change is made to the CI
            # configurations.
            log_test_reason(file_type, touched_file, test, options)
            return True
        elif file_type == "UNKNOWN":
            # Assume uncategorized source files can affect every test.
            log_test_reason(file_type, touched_file, test, options)
            return True
        elif file_type in ["TORCH", "CAFFE2", "TEST"]:
            parts = os.path.splitext(touched_file)[0].split(os.sep)
            touched_module = ".".join(parts)
            # test/ path does not have a "test." namespace
            if touched_module.startswith("test."):
                touched_module = touched_module.split("test.")[1]
            if touched_module in dep_modules or touched_module == test.replace(
                "/", "."
            ):
                log_test_reason(file_type, touched_file, test, options)
                return True

    # If nothing has determined the test has run, don't run the test.
    if options.verbose:
        print_to_stderr(f"Determination is skipping {test}")

    return False