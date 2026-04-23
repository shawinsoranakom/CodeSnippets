def merge(
    pr: GitHubPR,
    repo: GitRepo,
    comment_id: int,
    dry_run: bool = False,
    skip_mandatory_checks: bool = False,
    timeout_minutes: int = 400,
    stale_pr_days: int = 3,
    ignore_current: bool = False,
) -> None:
    initial_commit_sha = pr.last_commit_sha()
    pr_link = f"https://github.com/{pr.org}/{pr.project}/pull/{pr.pr_num}"
    print(f"Attempting merge of {initial_commit_sha} ({pr_link})")

    if MERGE_IN_PROGRESS_LABEL not in pr.get_labels():
        gh_add_labels(pr.org, pr.project, pr.pr_num, [MERGE_IN_PROGRESS_LABEL], dry_run)

    explainer = TryMergeExplainer(
        skip_mandatory_checks,
        pr.get_labels(),
        pr.pr_num,
        pr.org,
        pr.project,
        ignore_current,
    )

    # probably a bad name, but this is a list of current checks that should be
    # ignored and is toggled by the --ignore-current flag
    ignore_current_checks_info = []

    if pr.is_ghstack_pr():
        get_ghstack_prs(repo, pr)  # raises error if out of sync

    check_for_sev(pr.org, pr.project, skip_mandatory_checks)

    if skip_mandatory_checks:
        post_starting_merge_comment(repo, pr, explainer, dry_run)
        return pr.merge_into(
            repo,
            dry_run=dry_run,
            skip_mandatory_checks=skip_mandatory_checks,
            comment_id=comment_id,
        )

    # Check for approvals
    find_matching_merge_rule(pr, repo, skip_mandatory_checks=True)

    if not has_required_labels(pr):
        raise RuntimeError(LABEL_ERR_MSG.lstrip(" #"))

    if ignore_current:
        checks = pr.get_checkrun_conclusions()
        _, failing, _ = categorize_checks(
            checks,
            list(checks.keys()),
            ok_failed_checks_threshold=IGNORABLE_FAILED_CHECKS_THESHOLD,
        )
        ignore_current_checks_info = failing

    post_starting_merge_comment(
        repo,
        pr,
        explainer,
        dry_run,
        ignore_current_checks_info=ignore_current_checks_info,
    )

    start_time = time.time()
    last_exception = ""
    elapsed_time = 0.0
    ignore_current_checks = [
        x[0] for x in ignore_current_checks_info
    ]  # convert to List[str] for convenience
    while elapsed_time < timeout_minutes * 60:
        check_for_sev(pr.org, pr.project, skip_mandatory_checks)
        current_time = time.time()
        elapsed_time = current_time - start_time
        print(
            f"Attempting merge of https://github.com/{pr.org}/{pr.project}/pull/{pr.pr_num} ({elapsed_time / 60} minutes elapsed)"
        )
        pr = GitHubPR(pr.org, pr.project, pr.pr_num)
        if initial_commit_sha != pr.last_commit_sha():
            raise RuntimeError(
                "New commits were pushed while merging. Please rerun the merge command."
            )
        try:
            required_checks = []
            failed_rule_message = None
            ignore_flaky_failures = True
            try:
                find_matching_merge_rule(
                    pr, repo, ignore_current_checks=ignore_current_checks
                )
            except MandatoryChecksMissingError as ex:
                if ex.rule is not None:
                    ignore_flaky_failures = ex.rule.ignore_flaky_failures
                    if ex.rule.mandatory_checks_name is not None:
                        required_checks = ex.rule.mandatory_checks_name
                failed_rule_message = ex

            checks = pr.get_checkrun_conclusions()
            checks = get_classifications(
                pr.pr_num,
                pr.project,
                checks,
                ignore_current_checks=ignore_current_checks,
            )
            pending, failing, _ = categorize_checks(
                checks,
                required_checks + [x for x in checks if x not in required_checks],
                ok_failed_checks_threshold=IGNORABLE_FAILED_CHECKS_THESHOLD
                if ignore_flaky_failures
                else 0,
            )
            # HACK until GitHub will be better about surfacing those
            startup_failures = filter_checks_with_lambda(
                checks, lambda status: status == "STARTUP_FAILURE"
            )
            if len(startup_failures) > 0:
                raise RuntimeError(
                    f"{len(startup_failures)} STARTUP failures reported, please check workflows syntax! "
                    + ", ".join(f"[{x.name}]({x.url})" for x in startup_failures[:5])
                )
            # END of HACK

            if len(failing) > 0:
                raise RuntimeError(
                    f"{len(failing)} jobs have failed, first few of them are: "
                    + ", ".join(f"[{x[0]}]({x[1]})" for x in failing[:5])
                )
            if len(pending) > 0:
                if failed_rule_message is not None:
                    raise failed_rule_message
                else:
                    raise MandatoryChecksMissingError(
                        f"Still waiting for {len(pending)} jobs to finish, "
                        + f"first few of them are: {', '.join(x[0] for x in pending[:5])}"
                    )

            return pr.merge_into(
                repo,
                dry_run=dry_run,
                skip_mandatory_checks=skip_mandatory_checks,
                comment_id=comment_id,
                ignore_current_checks=ignore_current_checks,
            )
        except MandatoryChecksMissingError as ex:
            last_exception = str(ex)
            print(
                f"Merge of https://github.com/{pr.org}/{pr.project}/pull/{pr.pr_num} failed due to: {ex}. Retrying in 5 min",
                flush=True,
            )
            time.sleep(5 * 60)
    # Finally report timeout back
    msg = f"Merged timed out after {timeout_minutes} minutes. Please contact the pytorch_dev_infra team."
    msg += f"The last exception was: {last_exception}"
    gh_add_labels(pr.org, pr.project, pr.pr_num, ["land-failed"], dry_run)
    raise RuntimeError(msg)