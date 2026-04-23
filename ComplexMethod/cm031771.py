def get_unexpected_improvements(
    ignore_rules: set[IgnoreRule],
    files_with_warnings: dict[str, list[CompileWarning]],
) -> int:
    """
    Returns failure status if the number of warnings for a file is greater
    than the expected number of warnings for that file based on the ignore
    rules
    """
    unexpected_improvements = []
    for rule in ignore_rules:
        if (
            not rule.ignore_all
            and rule.file_path not in files_with_warnings.keys()
        ):
            if rule.file_path not in files_with_warnings.keys():
                unexpected_improvements.append((rule.file_path, rule.count, 0))
            elif len(files_with_warnings[rule.file_path]) < rule.count:
                unexpected_improvements.append((
                    rule.file_path,
                    rule.count,
                    len(files_with_warnings[rule.file_path]),
                ))

    if unexpected_improvements:
        print("Unexpected improvements:")
        for file in unexpected_improvements:
            print(f"{file[0]} expected {file[1]} warnings, found {file[2]}")
        return 1

    return 0