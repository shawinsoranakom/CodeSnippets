def do_revert_prs(
    repo: GitRepo,
    original_pr: GitHubPR,
    shas_and_prs: list[tuple[str, GitHubPR]],
    *,
    author_login: str,
    extra_msg: str = "",
    skip_internal_checks: bool = False,
    dry_run: bool = False,
) -> None:
    # Prepare and push revert commits
    for commit_sha, pr in shas_and_prs:
        revert_msg = f"\nReverted {pr.get_pr_url()} on behalf of {prefix_with_github_url(author_login)}"
        revert_msg += extra_msg
        repo.checkout(pr.default_branch())
        repo.revert(commit_sha)
        msg = repo.commit_message("HEAD")
        msg = re.sub(RE_PULL_REQUEST_RESOLVED, "", msg)
        msg += revert_msg
        repo.amend_commit_message(msg)
    repo.push(shas_and_prs[0][1].default_branch(), dry_run)

    # Comment/reopen PRs
    for commit_sha, pr in shas_and_prs:
        revert_message = ""
        if pr.pr_num == original_pr.pr_num:
            revert_message += (
                f"@{pr.get_pr_creator_login()} your PR has been successfully reverted."
            )
        else:
            revert_message += (
                f"@{pr.get_pr_creator_login()} your PR has been reverted as part of the stack under "
                f"#{original_pr.pr_num}.\n"
            )
        if (
            pr.has_internal_changes()
            and not pr.has_no_connected_diff()
            and not skip_internal_checks
        ):
            revert_message += "\n:warning: This PR might contain internal changes"
            revert_message += "\ncc: @pytorch/pytorch-dev-infra"
        gh_post_pr_comment(
            pr.org, pr.project, pr.pr_num, revert_message, dry_run=dry_run
        )

        pr.add_numbered_label("reverted", dry_run)
        pr.add_label("ci-no-td", dry_run)
        if not dry_run:
            gh_post_commit_comment(pr.org, pr.project, commit_sha, revert_msg)
            gh_update_pr_state(pr.org, pr.project, pr.pr_num)