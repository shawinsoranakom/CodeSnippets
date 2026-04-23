def fail_if_regression(
    warnings: list[str],
    files_with_expected_nits: set[str],
    files_with_nits: set[str],
) -> int:
    """
    Ensure some files always pass Sphinx nit-picky mode (no missing references).
    These are files which are *not* in .nitignore.
    """
    all_rst = {
        str(rst)
        for rst in Path("Doc/").rglob("*.rst")
        if rst.parts[1] not in EXCLUDE_SUBDIRS
    }
    should_be_clean = all_rst - files_with_expected_nits - EXCLUDE_FILES
    problem_files = sorted(should_be_clean & files_with_nits)
    if problem_files:
        print("\nError: must not contain warnings:\n")
        for filename in problem_files:
            print(filename)
            for warning in warnings:
                if filename in warning:
                    if match := WARNING_PATTERN.fullmatch(warning):
                        print("  {line}: {msg}".format_map(match))
        return -1
    return 0