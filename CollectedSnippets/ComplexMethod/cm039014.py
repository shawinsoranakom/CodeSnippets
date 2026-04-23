def group_files(changed_files: list[str]) -> dict[str, list[str]]:
    """
    Group changed files into different mypy calls.

    Args:
        changed_files: List of changed files.

    Returns:
        A dictionary mapping file group names to lists of changed files.
    """
    exclude_pattern = re.compile(f"^{'|'.join(EXCLUDE)}.*")
    file_groups = {"": []}
    file_groups.update({k: [] for k in SEPARATE_GROUPS})
    for changed_file in changed_files:
        # Skip files which should be ignored completely
        if exclude_pattern.match(changed_file):
            continue
        # Group files by mypy call
        for directory in SEPARATE_GROUPS:
            if re.match(f"^{directory}.*", changed_file):
                file_groups[directory].append(changed_file)
                break
        else:
            if changed_file.startswith("vllm/"):
                file_groups[""].append(changed_file)
    return file_groups