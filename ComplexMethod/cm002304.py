def infer_tests_to_run(output_file: str, diff_with_last_commit: bool = False, test_all: bool = False):
    """
    The main function called by the test fetcher. Determines the tests to run from the diff.

    Args:
        output_file (`str`):
            The path where to store the summary of the test fetcher analysis. Other files will be stored in the same
            folder:

            - examples_test_list.txt: The list of examples tests to run.
            - test_repo_utils.txt: Will indicate if the repo utils tests should be run or not.
            - doctest_list.txt: The list of doctests to run.

        diff_with_last_commit (`bool`, *optional*, defaults to `False`):
            Whether to analyze the diff with the last commit (for use on the main branch after a PR is merged) or with
            the branching point from main (for use on each PR).
    """
    if not test_all:
        modified_files = get_modified_python_files(diff_with_last_commit=diff_with_last_commit)
    else:
        modified_files = [str(k) for k in PATH_TO_TESTS.glob("*/*") if str(k).endswith(".py") and "test_" in str(k)]
        print("\n### test_all is TRUE, FETCHING ALL FILES###\n")
    print(f"\n### MODIFIED FILES ###\n{_print_list(modified_files)}")

    reverse_map = create_reverse_dependency_map()
    impacted_files = modified_files.copy()
    for f in modified_files:
        if f in reverse_map:
            impacted_files.extend(reverse_map[f])

    # Remove duplicates
    impacted_files = sorted(set(impacted_files))
    print(f"\n### IMPACTED FILES ###\n{_print_list(impacted_files)}")

    model_impacted = {"/".join(x.split("/")[:3]) for x in impacted_files if x.startswith("tests/models/")}
    # Grab the corresponding test files:
    if (
        any(file in CORE_FILES for file in modified_files)
        or len(model_impacted) >= NUM_MODELS_TO_TRIGGER_FULL_CI
        or commit_flags["test_all"]
    ):
        test_files_to_run = glob.glob("tests/**/test_**.py", recursive=True) + glob.glob(
            "examples/**/*.py", recursive=True
        )
        if len(model_impacted) >= NUM_MODELS_TO_TRIGGER_FULL_CI:
            print(
                f"More than {NUM_MODELS_TO_TRIGGER_FULL_CI - 1} models are impacted. CI is configured to test everything."
            )
    else:
        # All modified tests need to be run.
        test_files_to_run = [f for f in modified_files if f.startswith("tests") and "/test_" in f]
        impacted_files = get_impacted_files_from_tiny_model_summary(diff_with_last_commit=diff_with_last_commit)

        # Then we grab the corresponding test files.
        test_map = create_module_to_test_map(reverse_map=reverse_map)
        for f in modified_files + impacted_files:
            if f in test_map:
                test_files_to_run.extend(test_map[f])

    if should_run_repo_utils_tests(modified_files):
        test_files_to_run.extend(get_repo_utils_tests())

    test_files_to_run = sorted(set(test_files_to_run))
    # Remove SageMaker tests
    test_files_to_run = [f for f in test_files_to_run if f.split(os.path.sep)[1] != "sagemaker"]
    # Make sure we did not end up with a test file that was removed
    test_files_to_run = [f for f in test_files_to_run if (PATH_TO_REPO / f).exists()]

    print(f"\n### TEST TO RUN ###\n{_print_list(test_files_to_run)}")

    create_test_list_from_filter(test_files_to_run, out_path="test_preparation/")
    if len(test_files_to_run) < 20:
        doctest_list = get_doctest_files()
    else:
        doctest_list = []

    print(f"\n### DOCTEST TO RUN ###\n{_print_list(doctest_list)}")
    if doctest_list:
        doctest_file = Path(output_file).parent / "doctest_list.txt"
        with open(doctest_file, "w", encoding="utf-8") as f:
            f.write(" ".join(doctest_list))