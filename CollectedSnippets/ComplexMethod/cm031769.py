def parse_warning_ignore_file(file_path: str) -> set[IgnoreRule]:
    """
    Parses the warning ignore file and returns a set of IgnoreRules
    """
    files_with_expected_warnings: set[IgnoreRule] = set()
    with Path(file_path).open(encoding="UTF-8") as ignore_rules_file:
        files_with_expected_warnings = set()
        for i, line in enumerate(ignore_rules_file):
            line = line.strip()
            if line and not line.startswith("#"):
                line_parts = line.split()
                if len(line_parts) >= 2:
                    file_name = line_parts[0]
                    count = line_parts[1]
                    ignore_all = count == "*"
                    is_directory = file_name.endswith("/")

                    # Directories must have a wildcard count
                    if is_directory and count != "*":
                        print(
                            f"Error parsing ignore file: {file_path} "
                            f"at line: {i}"
                        )
                        print(
                            f"Directory {file_name} must have count set to *"
                        )
                        sys.exit(1)
                    if ignore_all:
                        count = "0"

                    files_with_expected_warnings.add(
                        IgnoreRule(
                            file_name, int(count), ignore_all, is_directory
                        )
                    )

    return files_with_expected_warnings