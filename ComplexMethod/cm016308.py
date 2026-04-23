def find_matched_symbols(
    symbols_regex: re.Pattern[str], test_globs: list[str] = CPP_TEST_GLOBS
) -> set[str]:
    """
    Goes through all lines not starting with // in the cpp files and
    accumulates a list of matches with the symbols_regex. Note that
    we expect symbols_regex to be sorted in reverse alphabetical
    order to allow superset regexes to get matched.
    """
    matched_symbols = set()
    # check noncommented out lines of the test files
    for cpp_test_glob in test_globs:
        for test_file in REPO_ROOT.glob(cpp_test_glob):
            with open(test_file) as tf:
                for test_file_line in tf:
                    test_file_line = test_file_line.strip()
                    if test_file_line.startswith(("//", "#")) or test_file_line == "":
                        continue
                    matches = re.findall(symbols_regex, test_file_line)
                    for m in matches:
                        if m != "":
                            matched_symbols.add(m)
    return matched_symbols