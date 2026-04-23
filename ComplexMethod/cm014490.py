def _revlist_to_prs(
    repo: GitRepo,
    pr: GitHubPR,
    rev_list: Iterable[str],
    should_skip: Callable[[int, GitHubPR], bool] | None = None,
) -> list[tuple[GitHubPR, str]]:
    rc: list[tuple[GitHubPR, str]] = []
    for idx, rev in enumerate(rev_list):
        msg = repo.commit_message(rev)
        # findall doesn't return named captures, so we need to use finditer
        all_matches = list(RE_PULL_REQUEST_RESOLVED.finditer(msg))
        if len(all_matches) != 1:
            raise RuntimeError(
                f"Found an unexpected number of PRs mentioned in commit {rev}: "
                f"{len(all_matches)}.  This is probably because you are using an "
                "old version of ghstack.  Please update ghstack and resubmit "
                "your PRs"
            )

        m = all_matches[0]
        if pr.org != m.group("owner") or pr.project != m.group("repo"):
            raise RuntimeError(
                f"PR {m.group('number')} resolved to wrong owner/repo pair"
            )
        pr_num = int(m.group("number"))
        candidate = GitHubPR(pr.org, pr.project, pr_num) if pr_num != pr.pr_num else pr
        if should_skip is not None and should_skip(idx, candidate):
            continue
        rc.append((candidate, rev))
    return rc