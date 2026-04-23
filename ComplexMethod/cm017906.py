def main(
    repo,
    token,
    pr_author,
    pr_body,
    pr_number,
    pr_title="",
    pr_created_at=None,
    autoclose=True,
    summary_file=None,
    gha_formatter=False,
):
    setup_logging(logger, gha_formatter)

    created_date = (
        datetime.fromisoformat(pr_created_at).date() if pr_created_at else None
    )
    if created_date is not None and created_date <= PR_TEMPLATE_DATE:
        logger.info(
            "PR #%s is older than PR template (%s) -- skipping all checks.",
            pr_number,
            PR_TEMPLATE_DATE,
        )
        return

    commit_count = get_recent_commit_count(
        pr_author, repo, token, since_days=365 * 3, max_count=5
    )
    if commit_count >= 5:
        logger.info(
            "PR #%s author is an established contributor -- skipping all checks.",
            pr_number,
        )
        return

    pr_title_result = SKIPPED
    total_changes = get_pr_total_changes(pr_number, repo, token)
    ticket_result = check_trac_ticket(pr_body, total_changes)
    ticket_status_result = SKIPPED
    ticket_has_patch_result = SKIPPED
    ticket_id = extract_ticket_id(pr_body) if ticket_result is None else None
    if ticket_id:
        pr_title_result = check_pr_title_has_ticket(pr_title, ticket_id)
        ticket_data = fetch_trac_ticket(ticket_id)
        ticket_status_result = check_trac_status(ticket_id, ticket_data)
        if ticket_status_result is None:
            # Polling is disabled (poll_timeout=0): has_patch is a non-fatal
            # warning, and contributors often update Trac after reviewing their
            # PR, making any fixed polling window unreliable.
            ticket_has_patch_result = check_trac_has_patch(
                ticket_id, ticket_data, poll_timeout=0
            )
        else:
            logger.info("Trac ticket is not Accepted -- skipping has_patch check.")
    else:
        logger.info("No Trac ticket -- skipping status and has_patch checks.")

    if created_date is not None and created_date <= AI_DISCLOSURE_DATE:
        ai_disclosure_result = SKIPPED
        logger.info(
            "PR #%s is older than AI Disclosure section (%s) -- skipping AI checks.",
            pr_number,
            AI_DISCLOSURE_DATE,
        )
    else:
        ai_disclosure_result = check_ai_disclosure(pr_body)

    results = [
        ("Trac ticket referenced", ticket_result, LEVEL_ERROR),
        ("Trac ticket is ready for work", ticket_status_result, LEVEL_ERROR),
        ("Trac ticket has_patch flag set", ticket_has_patch_result, LEVEL_WARNING),
        ("PR title includes ticket number", pr_title_result, LEVEL_WARNING),
        ("Branch description provided", check_branch_description(pr_body), LEVEL_ERROR),
        ("AI disclosure completed", ai_disclosure_result, LEVEL_ERROR),
        ("Checklist completed", check_checklist(pr_body), LEVEL_ERROR),
    ]
    write_job_summary(pr_number, results, summary_file)

    failures = [
        msg.as_details(level=level)
        for _, msg, level in results
        if msg is not None and msg is not SKIPPED and level == LEVEL_ERROR
    ]
    warning_msgs = [
        msg.as_details(level=level)
        for _, msg, level in results
        if msg is not None and msg is not SKIPPED and level == LEVEL_WARNING
    ]
    if not failures and not warning_msgs:
        logger.info("PR #%s passed all quality checks.", pr_number)
        return

    github_request(
        "POST",
        f"/issues/{pr_number}/comments",
        token,
        repo,
        {"body": "\n\n".join([CHECKS_HEADER, *failures, *warning_msgs, CHECKS_FOOTER])},
    )
    if not failures:
        logger.warning(
            "PR #%s has %s warning(s), adding informational comment.",
            pr_number,
            len(warning_msgs),
        )
        return

    msg = "PR #%s failed %s check(s), adding comment with details."
    if not autoclose or commit_count > 0:
        logger.warning(
            msg + " Not closing the PR given %s.",
            pr_number,
            len(failures),
            "warning-only mode" if not autoclose else "recent contributions",
        )
    else:
        logger.error(
            msg + " Closing the PR given lack of recent contributions.",
            pr_number,
            len(failures),
        )
        github_request("PATCH", f"/pulls/{pr_number}", token, repo, {"state": "closed"})
    return 1