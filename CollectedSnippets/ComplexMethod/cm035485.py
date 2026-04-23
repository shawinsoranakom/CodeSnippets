def get_changes_in_repo(repo_dir: str) -> list[dict[str, str]]:
    # Gets the status relative to the origin default branch - not the same as `git status`

    ref = get_valid_ref(repo_dir)
    if not ref:
        return []

    # Get changed files
    changed_files = run(
        f'git --no-pager diff --name-status {ref}', repo_dir
    ).splitlines()
    changes = []
    for line in changed_files:
        if not line.strip():
            raise RuntimeError(f'unexpected_value_in_git_diff:{changed_files}')

        # Handle different output formats from git diff --name-status
        # Depending on git config, format can be either:
        # * "A file.txt"
        # * "A       file.txt"
        # * "R100    old_file.txt    new_file.txt" (rename with similarity percentage)
        parts = line.split()
        if len(parts) < 2:
            raise RuntimeError(f'unexpected_value_in_git_diff:{changed_files}')

        status = parts[0].strip()

        # Handle rename operations (status starts with 'R' followed by similarity percentage)
        if status.startswith('R') and len(parts) == 3:
            # Rename: convert to delete (old path) + add (new path)
            old_path = parts[1].strip()
            new_path = parts[2].strip()
            changes.append(
                {
                    'status': 'D',
                    'path': old_path,
                }
            )
            changes.append(
                {
                    'status': 'A',
                    'path': new_path,
                }
            )
            continue

        # Handle copy operations (status starts with 'C' followed by similarity percentage)
        elif status.startswith('C') and len(parts) == 3:
            # Copy: only add the new path (original remains)
            new_path = parts[2].strip()
            changes.append(
                {
                    'status': 'A',
                    'path': new_path,
                }
            )
            continue

        # Handle regular operations (M, A, D, etc.)
        elif len(parts) == 2:
            path = parts[1].strip()
        else:
            raise RuntimeError(f'unexpected_value_in_git_diff:{changed_files}')

        if status == '??':
            status = 'A'
        elif status == '*':
            status = 'M'

        # Check for valid single-character status codes
        if status in {'M', 'A', 'D', 'U'}:
            changes.append(
                {
                    'status': status,
                    'path': path,
                }
            )
        else:
            raise RuntimeError(f'unexpected_status_in_git_diff:{changed_files}')

    # Get untracked files
    untracked_files = run(
        'git --no-pager ls-files --others --exclude-standard', repo_dir
    ).splitlines()
    for path in untracked_files:
        if path:
            changes.append({'status': 'A', 'path': path})

    return changes