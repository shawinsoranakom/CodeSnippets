def find_prs_between_commits(
    older_commit: str, newer_commit: str, repo_path: Path
) -> dict[int, dict]:
    """
    Find all PRs that went in between two commits.
    Returns a dictionary mapping PR numbers to their information.
    """
    print(f'Repository: {repo_path}', file=sys.stderr)
    print('Finding PRs between commits:', file=sys.stderr)
    print(f'  Older: {older_commit}', file=sys.stderr)
    print(f'  Newer: {newer_commit}', file=sys.stderr)
    print(file=sys.stderr)

    # Verify commits exist
    try:
        run_git_command(['git', 'rev-parse', '--verify', older_commit], repo_path)
        run_git_command(['git', 'rev-parse', '--verify', newer_commit], repo_path)
    except SystemExit:
        print('Error: One or both commits not found in repository', file=sys.stderr)
        sys.exit(1)

    # Extract PRs from the older commit itself (to exclude from results)
    # These PRs are already included at or before the older commit
    older_subject, older_body, _ = get_commit_info(older_commit, repo_path)
    older_message = f'{older_subject}\n{older_body}'
    excluded_prs = extract_pr_numbers_from_message(older_message)

    if excluded_prs:
        print(
            f'Excluding PRs already in older commit: {", ".join(f"#{pr}" for pr in sorted(excluded_prs))}',
            file=sys.stderr,
        )
        print(file=sys.stderr)

    # Get all commits between the two
    commits = get_commits_between(older_commit, newer_commit, repo_path)
    print(f'Found {len(commits)} commits to analyze', file=sys.stderr)
    print(file=sys.stderr)

    # Extract PR numbers from all commits
    pr_info: dict[int, dict] = {}
    commits_by_pr: dict[int, list[str]] = defaultdict(list)

    for commit_hash in commits:
        subject, body, author = get_commit_info(commit_hash, repo_path)
        full_message = f'{subject}\n{body}'

        pr_numbers = extract_pr_numbers_from_message(full_message)

        for pr_num in pr_numbers:
            # Skip PRs that are already in the older commit
            if pr_num in excluded_prs:
                continue

            commits_by_pr[pr_num].append(commit_hash)

            if pr_num not in pr_info:
                pr_info[pr_num] = {
                    'number': pr_num,
                    'first_commit': commit_hash[:8],
                    'first_commit_subject': subject,
                    'commits': [],
                    'github_info': None,
                }

            pr_info[pr_num]['commits'].append(
                {'hash': commit_hash[:8], 'subject': subject, 'author': author}
            )

    # Try to get additional info from GitHub API
    print('Fetching additional info from GitHub API...', file=sys.stderr)
    for pr_num in pr_info.keys():
        github_info = get_pr_info_from_github(pr_num, repo_path)
        if github_info:
            pr_info[pr_num]['github_info'] = github_info

    print(file=sys.stderr)

    return pr_info