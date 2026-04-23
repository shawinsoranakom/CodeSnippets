def extract_header_permalinks(lines: list[str]) -> list[HeaderPermalinkInfo]:
    """
    Extract list of header permalinks from the given lines.

    Return list of HeaderPermalinkInfo, where each dict contains:
    - `line_no` - line number (1-based)
    - `hashes` - string of hashes representing header level (e.g., "###")
    - `permalink` - permalink string (e.g., "{#permalink}")
    """

    headers: list[HeaderPermalinkInfo] = []
    in_code_block3 = False
    in_code_block4 = False

    for line_no, line in enumerate(lines, start=1):
        if not (in_code_block3 or in_code_block4):
            if line.startswith("```"):
                count = len(line) - len(line.lstrip("`"))
                if count == 3:
                    in_code_block3 = True
                    continue
                elif count >= 4:
                    in_code_block4 = True
                    continue

            header_match = HEADER_WITH_PERMALINK_RE.match(line)
            if header_match:
                hashes, title, permalink = header_match.groups()
                headers.append(
                    HeaderPermalinkInfo(
                        hashes=hashes, line_no=line_no, permalink=permalink, title=title
                    )
                )

        elif in_code_block3:
            if line.startswith("```"):
                count = len(line) - len(line.lstrip("`"))
                if count == 3:
                    in_code_block3 = False
                    continue

        elif in_code_block4:
            if line.startswith("````"):
                count = len(line) - len(line.lstrip("`"))
                if count >= 4:
                    in_code_block4 = False
                    continue

    return headers