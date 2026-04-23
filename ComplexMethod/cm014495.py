def try_revert(
    repo: GitRepo,
    pr: GitHubPR,
    *,
    dry_run: bool = False,
    comment_id: int | None = None,
    reason: str | None = None,
) -> None:
    try:
        author_login, commit_sha = validate_revert(repo, pr, comment_id=comment_id)
    except PostCommentError as e:
        gh_post_pr_comment(pr.org, pr.project, pr.pr_num, str(e), dry_run=dry_run)
        return

    extra_msg = f" due to {reason}" if reason is not None else ""
    extra_msg += (
        f" ([comment]({pr.get_comment_by_id(comment_id).url}))\n"
        if comment_id is not None
        else "\n"
    )
    shas_and_prs = [(commit_sha, pr)]
    if pr.is_ghstack_pr():
        try:
            shas_and_prs = get_ghstack_dependent_prs(repo, pr)
            prs_to_revert = " ".join([t[1].get_pr_url() for t in shas_and_prs])
            print(f"About to stack of PRs: {prs_to_revert}")
        except Exception as e:
            print(
                f"Failed to fetch dependent PRs: {str(e)}, fall over to single revert"
            )

    if not shas_and_prs:
        raise RuntimeError(
            f"No revertable PRs found in ghstack for #{pr.pr_num}. "
            f"This typically means the PR is still open (not merged) or "
            f"its GitHub state is inconsistent. Only closed/merged PRs can be reverted."
        )

    do_revert_prs(
        repo,
        pr,
        shas_and_prs,
        author_login=author_login,
        extra_msg=extra_msg,
        dry_run=dry_run,
        skip_internal_checks=can_skip_internal_checks(pr, comment_id),
    )