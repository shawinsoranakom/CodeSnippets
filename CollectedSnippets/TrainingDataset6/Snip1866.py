def extract_code_includes(lines: list[str]) -> list[CodeIncludeInfo]:
    """
    Extract lines that contain code includes.

    Return list of CodeIncludeInfo, where each dict contains:
    - `line_no` - line number (1-based)
    - `line` - text of the line
    """

    includes: list[CodeIncludeInfo] = []
    for line_no, line in enumerate(lines, start=1):
        if CODE_INCLUDE_RE.match(line):
            includes.append(CodeIncludeInfo(line_no=line_no, line=line))
    return includes