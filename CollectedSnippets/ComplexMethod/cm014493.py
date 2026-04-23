def get_ghstack_dependent_prs(
    repo: GitRepo, pr: GitHubPR, only_closed: bool = True
) -> list[tuple[str, GitHubPR]]:
    """
    Get the PRs in the stack that are above this PR (inclusive).
    Throws error if stack have branched or original branches are gone
    """
    if not pr.is_ghstack_pr():
        raise AssertionError(
            f"get_ghstack_dependent_prs called on non-ghstack PR #{pr.pr_num}"
        )
    orig_ref = f"{repo.remote}/{pr.get_ghstack_orig_ref()}"
    rev_list = repo.revlist(f"{pr.default_branch()}..{orig_ref}")
    if len(rev_list) == 0:
        raise RuntimeError(
            f"PR {pr.pr_num} does not have any revisions associated with it"
        )
    skip_len = len(rev_list) - 1
    for branch in repo.branches_containing_ref(orig_ref):
        candidate = repo.revlist(f"{pr.default_branch()}..{branch}")
        # Pick longest candidate
        if len(candidate) > len(rev_list):
            candidate, rev_list = rev_list, candidate
        # Validate that candidate always ends rev-list
        if rev_list[-len(candidate) :] != candidate:
            raise RuntimeError(
                f"Branch {branch} revlist {', '.join(candidate)} is not a subset of {', '.join(rev_list)}"
            )
    # Remove commits original PR depends on
    if skip_len > 0:
        rev_list = rev_list[:-skip_len]
    rc: list[tuple[str, GitHubPR]] = []
    for pr_, sha in _revlist_to_prs(repo, pr, rev_list):
        if not pr_.is_closed():
            if not only_closed:
                rc.append(("", pr_))
            continue
        commit_sha = get_pr_commit_sha(repo, pr_)
        rc.append((commit_sha, pr_))
    return rc