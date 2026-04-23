def main():
    if len(sys.argv) < 3:
        print('Usage: find_prs_between_commits <older_commit> <newer_commit> [options]')
        print()
        print('Arguments:')
        print('  <older_commit>  The older commit hash (or ref)')
        print('  <newer_commit>  The newer commit hash (or ref)')
        print()
        print('Options:')
        print('  --json          Output results in JSON format')
        print('  --repo <path>   Path to OpenHands repository (default: auto-detect)')
        print()
        print('Example:')
        print(
            '  find_prs_between_commits c79e0cd3c7a2501a719c9296828d7a31e4030585 35bddb14f15124a3dc448a74651a6592911d99e9'
        )
        print()
        print('Repository Detection:')
        print('  The script will try to find the OpenHands repository in this order:')
        print('  1. --repo argument')
        print('  2. Repository root (../../ from script location)')
        print('  3. Current directory')
        print('  4. OPENHANDS_REPO environment variable')
        print()
        print('Environment variables:')
        print(
            '  GITHUB_TOKEN    Optional. If set, will fetch additional PR info from GitHub API'
        )
        print('  OPENHANDS_REPO  Optional. Path to OpenHands repository')
        sys.exit(1)

    older_commit = sys.argv[1]
    newer_commit = sys.argv[2]
    json_output = '--json' in sys.argv

    # Check for --repo argument
    repo_path = None
    if '--repo' in sys.argv:
        repo_idx = sys.argv.index('--repo')
        if repo_idx + 1 < len(sys.argv):
            repo_path = Path(sys.argv[repo_idx + 1])
            if not (repo_path / '.git').exists():
                print(f'Error: {repo_path} is not a git repository', file=sys.stderr)
                sys.exit(1)

    # Auto-detect repository if not specified
    if repo_path is None:
        repo_path = find_openhands_repo()
        if repo_path is None:
            print('Error: Could not find OpenHands repository', file=sys.stderr)
            print('Please either:', file=sys.stderr)
            print(
                '  1. Place this script in .github/scripts/ within the OpenHands repository',
                file=sys.stderr,
            )
            print('  2. Run from the OpenHands repository directory', file=sys.stderr)
            print(
                '  3. Use --repo <path> to specify the repository location',
                file=sys.stderr,
            )
            print('  4. Set OPENHANDS_REPO environment variable', file=sys.stderr)
            sys.exit(1)

    # Find PRs
    pr_info = find_prs_between_commits(older_commit, newer_commit, repo_path)

    if json_output:
        # Output as JSON
        print(json.dumps(pr_info, indent=2))
    else:
        # Print results in human-readable format
        print_results(pr_info)

        # Also print a simple list for easy copying
        print(f'{"=" * 80}')
        print('PR Numbers (for easy copying):')
        print(f'{"=" * 80}')
        sorted_pr_nums = sorted(pr_info.keys())
        print(', '.join(f'#{pr}' for pr in sorted_pr_nums))