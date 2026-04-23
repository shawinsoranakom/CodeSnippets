def print_results(pr_info: dict[int, dict]):
    """Print the results in a readable format."""
    sorted_prs = sorted(pr_info.items(), key=lambda x: x[0])

    print(f'{"=" * 80}')
    print(f'Found {len(sorted_prs)} PRs')
    print(f'{"=" * 80}')
    print()

    for pr_num, info in sorted_prs:
        print(f'PR #{pr_num}')

        if info['github_info']:
            gh = info['github_info']
            print(f'  Title: {gh["title"]}')
            print(f'  Author: {gh["author"]["login"]}')
            print(f'  URL: {gh["url"]}')
            if gh.get('mergedAt'):
                print(f'  Merged: {gh["mergedAt"]}')
            if gh.get('baseRefName'):
                print(f'  Base: {gh["baseRefName"]} ← {gh["headRefName"]}')
        else:
            print(f'  Subject: {info["first_commit_subject"]}')

        # Show if this PR has multiple commits (cherry-picked or multiple commits)
        commit_count = len(info['commits'])
        if commit_count > 1:
            print(
                f'  ⚠️  Found {commit_count} commits (possible cherry-pick or multi-commit PR):'
            )
            for commit in info['commits'][:3]:  # Show first 3
                print(f'      {commit["hash"]}: {commit["subject"][:60]}')
            if commit_count > 3:
                print(f'      ... and {commit_count - 3} more')
        else:
            print(f'  Commit: {info["first_commit"]}')

        print()