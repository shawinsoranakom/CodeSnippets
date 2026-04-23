def get_unexpected_warnings(
    ignore_rules: set[IgnoreRule],
    files_with_warnings: dict[str, list[CompileWarning]],
) -> int:
    """
    Returns failure status if warnings discovered in list of warnings
    are associated with a file that is not found in the list of files
    with expected warnings
    """
    unexpected_warnings = {}
    for file in files_with_warnings.keys():
        rule = is_file_ignored(file, ignore_rules)

        if rule:
            if rule.ignore_all:
                continue

            if len(files_with_warnings[file]) > rule.count:
                unexpected_warnings[file] = (
                    files_with_warnings[file],
                    rule.count,
                )
            continue
        elif rule is None:
            # If the file is not in the ignore list, then it is unexpected
            unexpected_warnings[file] = (files_with_warnings[file], 0)

    if unexpected_warnings:
        print("Unexpected warnings:")
        for file in unexpected_warnings:
            print(
                f"{file} expected {unexpected_warnings[file][1]} warnings,"
                f" found {len(unexpected_warnings[file][0])}"
            )
            for warning in unexpected_warnings[file][0]:
                print(warning)

        return 1

    return 0