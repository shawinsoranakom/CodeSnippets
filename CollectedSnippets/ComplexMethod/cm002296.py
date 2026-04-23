def get_diff_for_doctesting(repo: Repo, base_commit: str, commits: list[str]) -> list[str]:
    """
    Get the diff in doc examples between a base commit and one or several commits.

    Args:
        repo (`git.Repo`):
            A git repository (for instance the Transformers repo).
        base_commit (`str`):
            The commit reference of where to compare for the diff. This is the current commit, not the branching point!
        commits (`List[str]`):
            The list of commits with which to compare the repo at `base_commit` (so the branching point).

    Returns:
        `List[str]`: The list of Python and Markdown files with a diff (files added or renamed are always returned, files
        modified are returned if the diff in the file is only in doctest examples).
    """
    print("\n### DIFF ###\n")
    code_diff = []
    for commit in commits:
        for diff_obj in commit.diff(base_commit):
            # We only consider Python files and doc files.
            if not diff_obj.b_path.endswith(".py") and not diff_obj.b_path.endswith(".md"):
                continue
            # We always add new python/md files
            if diff_obj.change_type == "A":
                code_diff.append(diff_obj.b_path)
            # Now for modified files
            elif diff_obj.change_type in ["M", "R"]:
                # In case of renames, we'll look at the tests using both the old and new name.
                if diff_obj.a_path != diff_obj.b_path:
                    code_diff.extend([diff_obj.a_path, diff_obj.b_path])
                else:
                    # Otherwise, we check modifications contain some doc example(s).
                    if diff_contains_doc_examples(repo, commit, diff_obj.b_path):
                        code_diff.append(diff_obj.a_path)
                    else:
                        print(f"Ignoring diff in {diff_obj.b_path} as it doesn't contain any doc example.")

    return code_diff