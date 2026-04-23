def categorize_checks(
    check_runs: JobNameToStateDict,
    required_checks: list[str],
    ok_failed_checks_threshold: int | None = None,
) -> tuple[
    list[tuple[str, str | None, int | None]],
    list[tuple[str, str | None, int | None]],
    dict[str, list[Any]],
]:
    """
    Categories all jobs into the list of pending and failing jobs. All known flaky
    failures and broken trunk are ignored by defaults when ok_failed_checks_threshold
    is not set (unlimited)
    """
    pending_checks: list[tuple[str, str | None, int | None]] = []
    failed_checks: list[tuple[str, str | None, int | None]] = []

    # failed_checks_categorization is used to keep track of all ignorable failures when saving the merge record on s3
    failed_checks_categorization: dict[str, list[Any]] = defaultdict(list)

    # If required_checks is not set or empty, consider all names are relevant
    relevant_checknames = [
        name
        for name in check_runs
        if not required_checks or any(x in name for x in required_checks)
    ]

    for checkname in required_checks:
        if all(checkname not in x for x in check_runs):
            pending_checks.append((checkname, None, None))

    for checkname in relevant_checknames:
        status = check_runs[checkname].status
        url = check_runs[checkname].url
        classification = check_runs[checkname].classification
        job_id = check_runs[checkname].job_id

        if status is None and classification != "UNSTABLE":
            # NB: No need to wait if the job classification is unstable as it would be
            # ignored anyway. This is useful to not need to wait for scarce resources
            # like ROCm, which is also frequently in unstable mode
            pending_checks.append((checkname, url, job_id))
        elif classification == "INVALID_CANCEL":
            continue
        elif not is_passing_status(check_runs[checkname].status):
            target = (
                failed_checks_categorization[classification]
                if classification
                in ("IGNORE_CURRENT_CHECK", "BROKEN_TRUNK", "FLAKY", "UNSTABLE")
                else failed_checks
            )
            target.append((checkname, url, job_id))

    flaky_or_broken_trunk = (
        failed_checks_categorization["BROKEN_TRUNK"]
        + failed_checks_categorization["FLAKY"]
    )

    if flaky_or_broken_trunk:
        warn(
            f"The following {len(flaky_or_broken_trunk)} checks failed but were likely due flakiness or broken trunk: "
            + ", ".join([x[0] for x in flaky_or_broken_trunk])
            + (
                f" but this is greater than the threshold of {ok_failed_checks_threshold} so merge will fail"
                if ok_failed_checks_threshold is not None
                and len(flaky_or_broken_trunk) > ok_failed_checks_threshold
                else ""
            )
        )

    if (
        ok_failed_checks_threshold is not None
        and len(flaky_or_broken_trunk) > ok_failed_checks_threshold
    ):
        failed_checks = failed_checks + flaky_or_broken_trunk

    # The list of failed_checks_categorization is returned so that it can be saved into the s3 merge record
    return (pending_checks, failed_checks, failed_checks_categorization)