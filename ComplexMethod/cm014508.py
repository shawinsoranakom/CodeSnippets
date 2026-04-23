def cherry_pick(
    github_actor: str,
    repo: GitRepo,
    pr: GitHubPR,
    commit_sha: str,
    onto_branch: str,
    classification: str,
    fixes: str,
    dry_run: bool = False,
) -> None:
    """
    Create a local branch to cherry pick the commit and submit it as a pull request
    """
    current_branch = repo.current_branch()
    cherry_pick_branch = create_cherry_pick_branch(
        github_actor, repo, pr, commit_sha, onto_branch
    )

    try:
        org, project = repo.gh_owner_and_name()

        cherry_pick_pr = ""
        if not dry_run:
            cherry_pick_pr = submit_pr(repo, pr, cherry_pick_branch, onto_branch)

        tracker_issues_comments = []
        tracker_issues = get_tracker_issues(org, project, onto_branch)
        for issue in tracker_issues:
            issue_number = int(str(issue.get("number", "0")))
            if not issue_number:
                continue

            res = cast(
                dict[str, Any],
                post_tracker_issue_comment(
                    org,
                    project,
                    issue_number,
                    pr.pr_num,
                    cherry_pick_pr,
                    classification,
                    fixes,
                    dry_run,
                ),
            )

            comment_url = res.get("html_url", "")
            if comment_url:
                tracker_issues_comments.append(comment_url)

        msg = f"The cherry pick PR is at {cherry_pick_pr}"
        if fixes:
            msg += f" and it is linked with issue {fixes}."
        elif classification in REQUIRES_ISSUE:
            msg += f" and it is recommended to link a {classification} cherry pick PR with an issue."

        if tracker_issues_comments:
            msg += " The following tracker issues are updated:\n"
            for tracker_issues_comment in tracker_issues_comments:
                msg += f"* {tracker_issues_comment}\n"

        post_pr_comment(org, project, pr.pr_num, msg, dry_run)

    finally:
        if current_branch:
            repo.checkout(branch=current_branch)