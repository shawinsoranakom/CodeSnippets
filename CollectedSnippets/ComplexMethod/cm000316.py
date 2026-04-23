def extract_conflict_info(tmpdir: str, stderr: str) -> tuple[list[str], list["ConflictInfo"]]:
    """Extract conflict information from git status."""
    status_result = run_git(["status", "--porcelain"], cwd=tmpdir, check=False)

    status_types = {
        'UU': 'content',
        'AA': 'both_added',
        'DD': 'both_deleted',
        'DU': 'deleted_by_us',
        'UD': 'deleted_by_them',
        'AU': 'added_by_us',
        'UA': 'added_by_them',
    }

    conflict_files = []
    conflict_details = []

    for line in status_result.stdout.split("\n"):
        if len(line) >= 3 and line[0:2] in status_types:
            status_code = line[0:2]
            file_path = line[3:].strip()
            conflict_files.append(file_path)

            info = analyze_conflict_markers(file_path, tmpdir)
            info.conflict_type = status_types.get(status_code, 'unknown')
            conflict_details.append(info)

    # Fallback to stderr parsing
    if not conflict_files and stderr:
        for line in stderr.split("\n"):
            if "CONFLICT" in line and ":" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    file_part = parts[-1].strip()
                    if file_part and not file_part.startswith("Merge"):
                        conflict_files.append(file_part)
                        conflict_details.append(ConflictInfo(path=file_part))

    return conflict_files, conflict_details