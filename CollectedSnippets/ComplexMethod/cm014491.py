def find_matching_merge_rule(
    pr: GitHubPR,
    repo: GitRepo | None = None,
    skip_mandatory_checks: bool = False,
    skip_internal_checks: bool = False,
    ignore_current_checks: list[str] | None = None,
) -> tuple[
    MergeRule,
    list[tuple[str, str | None, int | None]],
    list[tuple[str, str | None, int | None]],
    dict[str, list[Any]],
]:
    """
    Returns merge rule matching to this pr together with the list of associated pending
    and failing jobs OR raises an exception.

    NB: this function is used in Meta-internal workflows, see the comment at the top of
    this file for details.
    """
    changed_files = pr.get_changed_files()
    approved_by = set(pr.get_approved_by())

    issue_link = gen_new_issue_link(
        org=pr.org,
        project=pr.project,
        labels=["module: ci"],
    )
    reject_reason = f"No rule found to match PR. Please [report]{issue_link} this issue to DevX team."

    rules = read_merge_rules(repo, pr.org, pr.project)
    if not rules:
        reject_reason = f"Rejecting the merge as no rules are defined for the repository in {MERGE_RULE_PATH}"
        raise RuntimeError(reject_reason)

    checks = pr.get_checkrun_conclusions()
    checks = get_classifications(
        pr.pr_num,
        pr.project,
        checks,
        ignore_current_checks=ignore_current_checks,
    )

    # This keeps the list of all approvers that could stamp the change
    all_rule_approvers = {}

    # PRs can fail multiple merge rules, but it only needs to pass one rule to be approved.
    # If it fails all rules, we need to find the rule that it came closest to passing and report
    # that to the dev.
    #
    # reject_reason_score ranks rules by relevancy. The higher the score, the more relevant the
    # rule & rejection reason, and we only care about the most relevant rule/reason
    #
    # reject_reason_score intrepretation:
    # Score 0 to 10K - how many files rule matched
    # Score 10K - matched all files, but no overlapping approvers
    # Score 20K - matched all files and approvers, but mandatory checks are pending
    # Score 30k - Matched all files and approvers, but mandatory checks failed
    reject_reason_score = 0
    for rule in rules:
        rule_name = rule.name
        patterns_re = patterns_to_regex(rule.patterns)
        non_matching_files = []

        # Does this rule apply to all the files?
        for fname in changed_files:
            if not patterns_re.match(fname):
                non_matching_files.append(fname)
        if len(non_matching_files) > 0:
            num_matching_files = len(changed_files) - len(non_matching_files)
            if num_matching_files > reject_reason_score:
                reject_reason_score = num_matching_files
                reject_reason = "\n".join(
                    (
                        f"Not all files match rule `{rule_name}`.",
                        f"{num_matching_files} files matched, but there are still non-matching files:",
                        f"{','.join(non_matching_files[:5])}{', ...' if len(non_matching_files) > 5 else ''}",
                    )
                )
            continue

        # If rule needs approvers but PR has not been reviewed, skip it
        if len(rule.approved_by) > 0 and len(approved_by) == 0:
            if reject_reason_score < 10000:
                reject_reason_score = 10000
                reject_reason = f"PR #{pr.pr_num} has not been reviewed yet"
            continue

        # Does the PR have the required approvals for this rule?
        rule_approvers = set()
        for approver in rule.approved_by:
            if "/" in approver:
                org, name = approver.split("/")
                rule_approvers.update(gh_get_team_members(org, name))
            else:
                rule_approvers.add(approver)
        approvers_intersection = approved_by.intersection(rule_approvers)
        # If rule requires approvers but they aren't the ones that reviewed PR
        if len(approvers_intersection) == 0 and len(rule_approvers) > 0:
            # Less than or equal is intentionally used here to gather all potential
            # approvers
            if reject_reason_score <= 10000:
                reject_reason_score = 10000

                all_rule_approvers[rule.name] = rule.approved_by
                # Prepare the reject reason
                all_rule_approvers_msg = [
                    f"- {name} ({', '.join(approved_by[:5])}{', ...' if len(approved_by) > 5 else ''})"
                    for name, approved_by in all_rule_approvers.items()
                ]

                reject_reason = "Approvers from one of the following sets are needed:\n"
                reject_reason += "\n".join(all_rule_approvers_msg)

            continue

        # Does the PR pass the checks required by this rule?
        mandatory_checks = (
            rule.mandatory_checks_name if rule.mandatory_checks_name is not None else []
        )
        required_checks = list(
            filter(
                lambda x: ("EasyCLA" in x)
                or ("Facebook CLA Check" in x)
                or not skip_mandatory_checks,
                mandatory_checks,
            )
        )
        pending_checks, failed_checks, _ = categorize_checks(
            checks,
            required_checks,
            ok_failed_checks_threshold=IGNORABLE_FAILED_CHECKS_THESHOLD
            if rule.ignore_flaky_failures
            else 0,
        )

        # categorize_checks assumes all tests are required if required_checks is empty.
        # this is a workaround as we want to keep that behavior for categorize_checks
        # generally.
        if not required_checks:
            pending_checks = []
            failed_checks = []

        hud_link = f"https://hud.pytorch.org/{pr.org}/{pr.project}/commit/{pr.last_commit_sha()}"
        if len(failed_checks) > 0:
            if reject_reason_score < 30000:
                reject_reason_score = 30000
                reject_reason = "\n".join(
                    (
                        f"{len(failed_checks)} mandatory check(s) failed.  The first few are:",
                        *checks_to_markdown_bullets(failed_checks),
                        "",
                        f"Dig deeper by [viewing the failures on hud]({hud_link})",
                    )
                )
            continue
        elif len(pending_checks) > 0:
            if reject_reason_score < 20000:
                reject_reason_score = 20000
                reject_reason = "\n".join(
                    (
                        f"{len(pending_checks)} mandatory check(s) are pending/not yet run.  The first few are:",
                        *checks_to_markdown_bullets(pending_checks),
                        "",
                        f"Dig deeper by [viewing the pending checks on hud]({hud_link})",
                    )
                )
            continue

        if not skip_internal_checks and pr.has_internal_changes():
            raise RuntimeError(
                "This PR has internal changes and must be landed via Phabricator! Please try reimporting/rexporting the PR!"
            )

        # Categorize all checks when skip_mandatory_checks (force merge) is set. Do it here
        # where the list of checks is readily available. These records will be saved into
        # s3 merge records
        (
            pending_mandatory_checks,
            failed_mandatory_checks,
            ignorable_checks,
        ) = categorize_checks(
            checks,
            [],
            ok_failed_checks_threshold=IGNORABLE_FAILED_CHECKS_THESHOLD,
        )
        return (
            rule,
            pending_mandatory_checks,
            failed_mandatory_checks,
            ignorable_checks,
        )

    if reject_reason_score == 20000:
        raise MandatoryChecksMissingError(reject_reason, rule)
    raise MergeRuleFailedError(reject_reason, rule)