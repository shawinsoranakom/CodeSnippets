def delete_branches() -> None:
    now = datetime.now().timestamp()
    git_repo = GitRepo(str(REPO_ROOT), "origin", debug=True)
    branches = get_branches(git_repo)
    prs_by_branch = get_recent_prs()
    keep_branches = get_branches_with_magic_label_or_open_pr()

    delete = []
    # Do not delete if:
    # * associated PR is open, closed but updated recently, or contains the magic string
    # * no associated PR and branch was updated in last 1.5 years
    # * is protected
    # Setting different values of PR_WINDOW will change how branches with closed
    # PRs are treated depending on how old the branch is.  The default value of
    # 90 will allow branches with closed PRs to be deleted if the PR hasn't been
    # updated in 90 days and the branch hasn't been updated in 1.5 years
    for base_branch, (date, sub_branches) in branches.items():
        print(f"[{base_branch}] Updated {(now - date) / SEC_IN_DAY} days ago")
        if base_branch in keep_branches:
            print(f"[{base_branch}] Has magic label or open PR, skipping")
            continue
        pr = prs_by_branch.get(base_branch)
        if pr:
            print(
                f"[{base_branch}] Has PR {pr['number']}: {pr['state']}, updated {(now - pr['updatedAt']) / SEC_IN_DAY} days ago"
            )
            if (
                now - pr["updatedAt"] < CLOSED_PR_RETENTION
                or (now - date) < CLOSED_PR_RETENTION
            ):
                continue
        elif now - date < NO_PR_RETENTION:
            continue
        print(f"[{base_branch}] Checking for branch protections")
        if any(is_protected(sub_branch) for sub_branch in sub_branches):
            print(f"[{base_branch}] Is protected")
            continue
        for sub_branch in sub_branches:
            print(f"[{base_branch}] Deleting {sub_branch}")
            delete.append(sub_branch)
        if ESTIMATED_TOKENS[0] > 400:
            print("Estimated tokens exceeded, exiting")
            break

    print(f"To delete ({len(delete)}):")
    for branch in delete:
        print(f"About to delete branch {branch}")
        delete_branch(git_repo, branch)