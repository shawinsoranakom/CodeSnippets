def check_perf(actual_csv, expected_csv, expected_filename, threshold):
    failed = []
    improved = []
    baseline_not_found = []

    actual_csv = actual_csv[~actual_csv["Case Name"].isin(set(SKIP_TEST_LISTS))]

    for case in actual_csv["Case Name"]:
        perf = get_field(actual_csv, case, "Execution Time")
        expected_perf = get_field(expected_csv, case, "Execution Time")

        if expected_perf is None:
            status = "Baseline Not Found"
            print(f"{case:34}  {status}")
            baseline_not_found.append(case)
            continue

        speed_up = expected_perf / perf

        if (1 - threshold) <= speed_up < (1 + threshold):
            status = "PASS"
            print(f"{case:34}  {status}")
            continue
        elif speed_up >= 1 + threshold:
            status = "IMPROVED:"
            improved.append(case)
        else:
            status = "FAILED:"
            failed.append(case)
        print(f"{case:34}  {status:9} perf={perf}, expected={expected_perf}")

    msg = ""
    if failed or improved or baseline_not_found:
        if failed:
            msg += textwrap.dedent(
                f"""
            Error: {len(failed)} models have performance status regressed:
                {" ".join(failed)}

            """
            )
        if improved:
            msg += textwrap.dedent(
                f"""
            Improvement: {len(improved)} models have performance status improved:
                {" ".join(improved)}

            """
            )

        if baseline_not_found:
            msg += textwrap.dedent(
                f"""
            Baseline Not Found: {len(baseline_not_found)} models don't have the baseline data:
                {" ".join(baseline_not_found)}

            """
            )

        msg += textwrap.dedent(
            f"""
        If this change is expected, you can update `{expected_filename}` to reflect the new baseline.
        """
        )
    return failed or improved or baseline_not_found, msg