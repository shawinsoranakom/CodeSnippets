def process_jobs(
    workflow: str,
    job_name: str,
    test_matrix: dict[str, list[Any]],
    issue_type: IssueType,
    url: str,
) -> dict[str, list[Any]]:
    """
    Both disabled and unstable jobs are in the following format:

    {
        "WORKFLOW / PLATFORM / JOB (CONFIG)": [
            AUTHOR,
            ISSUE_NUMBER,
            ISSUE_URL,
            WORKFLOW,
            PLATFORM,
            JOB (CONFIG),
        ],
        "pull / linux-bionic-py3.8-clang9 / test (dynamo)": [
            "pytorchbot",
            "94861",
            "https://github.com/pytorch/pytorch/issues/94861",
            "pull",
            "linux-bionic-py3.8-clang9",
            "test (dynamo)",
        ],
    }
    """
    try:
        # The job name from github is in the PLATFORM / JOB (CONFIG) format, so breaking
        # it into its two components first
        current_platform, _ = (n.strip() for n in job_name.split(JOB_NAME_SEP, 1) if n)
    except ValueError:
        warnings.warn(f"Invalid job name {job_name}, returning")
        return test_matrix

    for record in download_json(url=url, headers={}).values():
        (
            author,
            _,
            target_url,
            target_workflow,
            target_platform,
            target_job_cfg,
        ) = record

        if target_workflow != workflow:
            # The current workflow doesn't match this record
            continue

        cleanup_regex = rf"(-{BUILD_JOB_NAME}|-{TEST_JOB_NAME})$"
        # There is an exception here for binary build workflows in which the platform
        # names have the build and test suffix. For example, we have a build job called
        # manywheel-py3-cuda11_8-build / build and its subsequent test job called
        # manywheel-py3-cuda11_8-test / test. So they are linked, but their suffixes
        # are different
        target_platform_no_suffix = re.sub(cleanup_regex, "", target_platform)
        current_platform_no_suffix = re.sub(cleanup_regex, "", current_platform)

        if (
            target_platform != current_platform
            and target_platform_no_suffix != current_platform_no_suffix
        ):
            # The current platform doesn't match this record
            continue

        # The logic after this is fairly complicated:
        #
        # - If the target record doesn't have the optional job (config) name,
        #   i.e. pull / linux-bionic-py3.8-clang9, all build and test jobs will
        #   be skipped if it's a disabled record or marked as unstable if it's
        #   an unstable record
        #
        # - If the target record has the job name and it's a build job, i.e.
        #   pull / linux-bionic-py3.8-clang9 / build, all build and test jobs
        #   will be skipped if it's a disabled record or marked as unstable if
        #   it's an unstable record, because the latter requires the former
        #
        # - If the target record has the job name and it's a test job without
        #   the config part, i.e. pull / linux-bionic-py3.8-clang9 / test, all
        #   test jobs will be skipped if it's a disabled record or marked as
        #   unstable if it's an unstable record
        #
        # - If the target record has the job (config) name, only that test config
        #   will be skipped or marked as unstable
        if not target_job_cfg:
            msg = (
                f"Issue {target_url} created by {author} has {issue_type.value} "
                + f"all CI jobs for {workflow} / {job_name}"
            )
            info(msg)
            return _filter_jobs(
                test_matrix=test_matrix,
                issue_type=issue_type,
            )

        if target_job_cfg == BUILD_JOB_NAME:
            msg = (
                f"Issue {target_url} created by {author} has {issue_type.value} "
                + f"the build job for {workflow} / {job_name}"
            )
            info(msg)
            return _filter_jobs(
                test_matrix=test_matrix,
                issue_type=issue_type,
            )

        if target_job_cfg in (TEST_JOB_NAME, BUILD_AND_TEST_JOB_NAME):
            msg = (
                f"Issue {target_url} created by {author} has {issue_type.value} "
                + f"all the test jobs for {workflow} / {job_name}"
            )
            info(msg)
            return _filter_jobs(
                test_matrix=test_matrix,
                issue_type=issue_type,
            )

        m = JOB_NAME_CFG_REGEX.match(target_job_cfg)
        if m:
            target_job = m.group("job")
            # Make sure that the job name is a valid test job name first before checking the config
            if target_job in (TEST_JOB_NAME, BUILD_AND_TEST_JOB_NAME):
                target_cfg = m.group("cfg")

                # NB: There can be multiple unstable configurations, i.e. inductor, inductor_huggingface
                test_matrix = _filter_jobs(
                    test_matrix=test_matrix,
                    issue_type=issue_type,
                    target_cfg=target_cfg,
                )
        else:
            warnings.warn(
                f"Found a matching {issue_type.value} issue {target_url} for {workflow} / {job_name}, "
                + f"but the name {target_job_cfg} is invalid"
            )

    # Found no matching target, return the same input test matrix
    return test_matrix