def clean_doctest_list(doctest_file: str, overwrite: bool = False):
    """
    Cleans the doctest in a given file.

    Args:
        doctest_file (`str`):
            The path to the doctest file to check or clean.
        overwrite (`bool`, *optional*, defaults to `False`):
            Whether or not to fix problems. If `False`, will error when the file is not clean.
    """
    non_existent_paths = []
    all_paths = []
    with open(doctest_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().split(" ")[0]
            path = os.path.join(REPO_PATH, line)
            if not (os.path.isfile(path) or os.path.isdir(path)):
                non_existent_paths.append(line)
            all_paths.append(line)

    if len(non_existent_paths) > 0:
        non_existent_paths = "\n".join([f"- {f}" for f in non_existent_paths])
        raise ValueError(f"`{doctest_file}` contains non-existent paths:\n{non_existent_paths}")

    sorted_paths = sorted(all_paths)
    if all_paths != sorted_paths:
        if not overwrite:
            raise ValueError(
                f"Files in `{doctest_file}` are not in alphabetical order, run `make fix-repo` to fix "
                "this automatically."
            )
        with open(doctest_file, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted_paths) + "\n")