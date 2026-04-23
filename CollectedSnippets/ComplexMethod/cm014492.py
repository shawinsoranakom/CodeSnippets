def get_classifications(
    pr_num: int,
    project: str,
    checks: dict[str, JobCheckState],
    ignore_current_checks: list[str] | None,
) -> dict[str, JobCheckState]:
    # Get the failure classification from Dr.CI, which is the source of truth
    # going forward. It's preferable to try calling Dr.CI API directly first
    # to get the latest results as well as update Dr.CI PR comment
    drci_classifications = get_drci_classifications(pr_num=pr_num, project=project)

    def get_readable_drci_results(drci_classifications: Any) -> str:
        try:
            s = f"From Dr.CI API ({pr_num}):\n"
            for classification, jobs in drci_classifications.items():
                s += f"  {classification}: \n"
                for job in jobs:
                    s += f"    {job['id']} {job['name']}\n"
            return s
        except Exception:
            return f"From Dr.CI API: {json.dumps(drci_classifications)}"

    print(get_readable_drci_results(drci_classifications))

    # NB: if the latest results from Dr.CI is not available, i.e. when calling from
    # SandCastle, we fallback to any results we can find on Dr.CI check run summary
    if (
        not drci_classifications
        and DRCI_CHECKRUN_NAME in checks
        and checks[DRCI_CHECKRUN_NAME]
        and checks[DRCI_CHECKRUN_NAME].summary
    ):
        drci_summary = checks[DRCI_CHECKRUN_NAME].summary
        try:
            print(f"From Dr.CI checkrun summary: {drci_summary}")
            drci_classifications = json.loads(str(drci_summary))
        except json.JSONDecodeError:
            warn("Invalid Dr.CI checkrun summary")
            drci_classifications = {}

    checks_with_classifications = checks.copy()
    for name, check in checks.items():
        if check.status == "SUCCESS" or check.status == "NEUTRAL":
            continue

        if is_unstable(check, drci_classifications):
            checks_with_classifications[name] = JobCheckState(
                check.name,
                check.url,
                check.status,
                "UNSTABLE",
                check.job_id,
                check.title,
                check.summary,
            )
            continue

        # NB: It's important to note that when it comes to ghstack and broken trunk classification,
        # Dr.CI uses the base of the whole stack
        if is_broken_trunk(check, drci_classifications):
            checks_with_classifications[name] = JobCheckState(
                check.name,
                check.url,
                check.status,
                "BROKEN_TRUNK",
                check.job_id,
                check.title,
                check.summary,
            )
            continue

        elif is_flaky(check, drci_classifications):
            checks_with_classifications[name] = JobCheckState(
                check.name,
                check.url,
                check.status,
                "FLAKY",
                check.job_id,
                check.title,
                check.summary,
            )
            continue

        elif is_invalid_cancel(name, check.status, drci_classifications):
            # NB: Create a new category here for invalid cancelled signals because
            # there are usually many of them when they happen. So, they shouldn't
            # be counted toward ignorable failures threshold
            checks_with_classifications[name] = JobCheckState(
                check.name,
                check.url,
                check.status,
                "INVALID_CANCEL",
                check.job_id,
                check.title,
                check.summary,
            )
            continue

        if ignore_current_checks is not None and name in ignore_current_checks:
            checks_with_classifications[name] = JobCheckState(
                check.name,
                check.url,
                check.status,
                "IGNORE_CURRENT_CHECK",
                check.job_id,
                check.title,
                check.summary,
            )

    return checks_with_classifications