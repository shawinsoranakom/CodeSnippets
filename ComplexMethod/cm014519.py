def perform_misc_tasks(
    labels: set[str],
    test_matrix: dict[str, list[Any]],
    job_name: str,
    pr_body: str,
    branch: str | None = None,
    tag: str | None = None,
) -> None:
    """
    In addition to apply the filter logic, the script also does the following
    misc tasks to set keep-going and is-unstable variables
    """
    set_output(
        "keep-going",
        branch == MAIN_BRANCH
        or bool(tag and re.match(r"^trunk/[a-f0-9]{40}$", tag))
        # Pattern for tags created via manual run on HUD
        or bool(tag and re.match(r"^ciflow/[^/]+/[a-f0-9]{40}$", tag))
        or check_for_setting(labels, pr_body, "keep-going"),
    )
    set_output(
        "ci-verbose-test-logs",
        check_for_setting(labels, pr_body, "ci-verbose-test-logs"),
    )
    set_output(
        "ci-test-showlocals", check_for_setting(labels, pr_body, "ci-test-showlocals")
    )
    set_output(
        "ci-no-test-timeout", check_for_setting(labels, pr_body, "ci-no-test-timeout")
    )
    set_output("ci-no-td", check_for_setting(labels, pr_body, "ci-no-td"))
    # Only relevant for the one linux distributed cuda job, delete this when TD
    # is rolled out completely
    set_output(
        "ci-td-distributed", check_for_setting(labels, pr_body, "ci-td-distributed")
    )

    # Obviously, if the job name includes unstable, then this is an unstable job
    is_unstable = job_name and IssueType.UNSTABLE.value in job_name
    if not is_unstable and test_matrix and test_matrix.get("include"):
        # Even when the job name doesn't mention unstable, we will also mark it as
        # unstable when the test matrix only includes unstable jobs. Basically, this
        # logic allows build or build-and-test jobs to be marked as unstable too.
        #
        # Basically, when a build job is unstable, all the subsequent test jobs are
        # also unstable. And when all test jobs are unstable, we will also treat the
        # build job as unstable. It's simpler this way
        is_unstable = all(IssueType.UNSTABLE.value in r for r in test_matrix["include"])

    set_output(
        "is-unstable",
        is_unstable,
    )

    set_output("reenabled-issues", ",".join(get_reenabled_issues(pr_body=pr_body)))

    if MEM_LEAK_LABEL in labels:
        # Enable mem leak check if label is added
        for config in test_matrix.get("include", []):
            if is_cuda_or_rocm_job(job_name):
                config["mem_leak_check"] = "mem_leak_check"