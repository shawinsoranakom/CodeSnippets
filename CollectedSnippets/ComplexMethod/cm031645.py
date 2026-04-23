def scan_file_for_docs(
    filename: str,
    text: str,
    names: set[str]) -> tuple[list[str], list[str]]:
    """
    Scan a header file for  C API functions.
    """
    undocumented: list[str] = []
    documented_ignored: list[str] = []
    colors = _colorize.get_colors()

    def check_for_name(name: str) -> None:
        documented = name in names
        if documented and (name in IGNORED):
            documented_ignored.append(name)
        elif not documented and (name not in IGNORED):
            undocumented.append(name)

    for function in SIMPLE_FUNCTION_REGEX.finditer(text):
        name = function.group(2)
        if not API_NAME_REGEX.fullmatch(name):
            continue

        check_for_name(name)

    for macro in SIMPLE_MACRO_REGEX.finditer(text):
        name = macro.group(1)
        if not API_NAME_REGEX.fullmatch(name):
            continue

        if "(" in name:
            name = name[: name.index("(")]

        check_for_name(name)

    for inline in SIMPLE_INLINE_REGEX.finditer(text):
        name = inline.group(2)
        if not API_NAME_REGEX.fullmatch(name):
            continue

        check_for_name(name)

    for data in SIMPLE_DATA_REGEX.finditer(text):
        name = data.group(1)
        if not API_NAME_REGEX.fullmatch(name):
            continue

        check_for_name(name)

    # Remove duplicates and sort alphabetically to keep the output deterministic
    undocumented = list(set(undocumented))
    undocumented.sort()

    if undocumented or documented_ignored:
        print(f"{filename} {colors.RED}BAD{colors.RESET}")
        for name in undocumented:
            print(f"{colors.BOLD_RED}UNDOCUMENTED:{colors.RESET} {name}")
        for name in documented_ignored:
            print(f"{colors.BOLD_YELLOW}DOCUMENTED BUT IGNORED:{colors.RESET} {name}")
    else:
        print(f"{filename} {colors.GREEN}OK{colors.RESET}")

    return undocumented, documented_ignored