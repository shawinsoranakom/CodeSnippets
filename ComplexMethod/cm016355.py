def save_results(
    workflow_id: int,
    workflow_run_attempt: int,
    all_tests: dict[str, dict[str, int]],
) -> None:
    """
    Save the result to S3, which then gets put into the HUD backend database
    """
    should_be_enabled_tests = {
        name: stats
        for name, stats in all_tests.items()
        if "num_green" in stats
        and stats["num_green"]
        and "num_red" in stats
        and stats["num_red"] == 0
    }
    still_flaky_tests = {
        name: stats
        for name, stats in all_tests.items()
        if name not in should_be_enabled_tests
    }

    records = {}
    for test_id, stats in all_tests.items():
        num_green = stats.get("num_green", 0)
        num_red = stats.get("num_red", 0)
        disabled_test_name, name, classname, filename = get_disabled_test_name(test_id)

        key, record = prepare_record(
            workflow_id=workflow_id,
            workflow_run_attempt=workflow_run_attempt,
            name=name,
            classname=classname,
            filename=filename,
            flaky=test_id in still_flaky_tests,
            num_green=num_green,
            num_red=num_red,
        )
        records[key] = record

    # Log the results
    print(f"The following {len(should_be_enabled_tests)} tests should be re-enabled:")
    for test_id, stats in should_be_enabled_tests.items():
        disabled_test_name, name, classname, filename = get_disabled_test_name(test_id)
        print(f"  {disabled_test_name} from {filename}")

    print(f"The following {len(still_flaky_tests)} are still flaky:")
    for test_id, stats in still_flaky_tests.items():
        num_green = stats.get("num_green", 0)
        num_red = stats.get("num_red", 0)

        disabled_test_name, name, classname, filename = get_disabled_test_name(test_id)
        print(
            f"  {disabled_test_name} from {filename}, failing {num_red}/{num_red + num_green}"
        )

    upload_workflow_stats_to_s3(
        workflow_id,
        workflow_run_attempt,
        "rerun_disabled_tests",
        list(records.values()),
    )