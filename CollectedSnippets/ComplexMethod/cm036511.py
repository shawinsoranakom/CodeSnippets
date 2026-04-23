def get_filtered_test_settings(
    test_settings: dict[str, VLMTestInfo],
    test_type: VLMTestType,
    new_proc_per_test: bool,
) -> dict[str, VLMTestInfo]:
    """Given the dict of potential test settings to run, return a subdict
    of tests who have the current test type enabled with the matching val for
    fork_per_test.
    """

    def matches_test_type(test_info: VLMTestInfo, test_type: VLMTestType):
        return test_info.test_type == test_type or (
            isinstance(test_info.test_type, Iterable)
            and test_type in test_info.test_type
        )

    matching_tests = {}
    for test_name, test_info in test_settings.items():
        # Otherwise check if the test has the right type & keep if it does
        if matches_test_type(test_info, test_type):
            # Embedding tests need to have a conversion func in their test info
            if matches_test_type(test_info, VLMTestType.EMBEDDING):
                assert test_info.convert_assets_to_embeddings is not None
            # Custom test inputs need to explicitly define the mm limit/inputs
            if matches_test_type(test_info, VLMTestType.CUSTOM_INPUTS):
                assert test_info.custom_test_opts is not None and isinstance(
                    test_info.custom_test_opts, Iterable
                )
            # For all types besides custom inputs, we need a prompt formatter
            else:
                assert test_info.prompt_formatter is not None

            # Everything looks okay; keep if this is correct proc handling
            if (
                test_info.distributed_executor_backend is not None
            ) == new_proc_per_test:
                matching_tests[test_name] = test_info

    return matching_tests