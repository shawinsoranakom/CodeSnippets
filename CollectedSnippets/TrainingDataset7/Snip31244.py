def paired_tests(paired_test, options, test_labels, start_at, start_after):
    if not test_labels:
        test_labels = collect_test_modules(start_at, start_after)

    print("***** Trying paired execution")

    # Make sure the constant member of the pair isn't in the test list
    # Also remove tests that need to be run in specific combinations
    for label in [paired_test, "model_inheritance_same_model_name"]:
        try:
            test_labels.remove(label)
        except ValueError:
            pass

    subprocess_args = get_subprocess_args(options)

    for i, label in enumerate(test_labels):
        print(
            "***** %d of %d: Check test pairing with %s"
            % (i + 1, len(test_labels), label)
        )
        failures = subprocess.call(subprocess_args + [label, paired_test])
        if failures:
            print("***** Found problem pair with %s" % label)
            return

    print("***** No problem pair found")