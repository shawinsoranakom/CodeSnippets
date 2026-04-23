def parse_diff_block(diff_block: str) -> dict:
    """
    Parses a block of diff text into a Diff object.

    Args:
    - diff_block (str): A single block of diff text.

    Returns:
    - dict: A dictionary containing a single Diff object keyed by the post-edit filename.
    """
    lines = diff_block.strip().split("\n")[1:-1]  # Exclude the opening and closing ```
    diffs = {}
    current_diff = None
    hunk_lines = []
    filename_pre = None
    filename_post = None
    hunk_header = None

    for line in lines:
        if line.startswith("--- "):
            # Pre-edit filename
            filename_pre = line[4:]
        elif line.startswith("+++ "):
            # Post-edit filename and initiation of a new Diff object
            if (
                filename_post is not None
                and current_diff is not None
                and hunk_header is not None
            ):
                current_diff.hunks.append(Hunk(*hunk_header, hunk_lines))
                hunk_lines = []
            filename_post = line[4:]
            current_diff = Diff(filename_pre, filename_post)
            diffs[filename_post] = current_diff
        elif line.startswith("@@ "):
            # Start of a new hunk in the diff
            if hunk_lines and current_diff is not None and hunk_header is not None:
                current_diff.hunks.append(Hunk(*hunk_header, hunk_lines))
                hunk_lines = []
            hunk_header = parse_hunk_header(line)
        elif line.startswith("+"):
            # Added line
            hunk_lines.append((ADD, line[1:]))
        elif line.startswith("-"):
            # Removed line
            hunk_lines.append((REMOVE, line[1:]))
        else:
            # Retained line
            hunk_lines.append((RETAIN, line[1:]))

    # Append the last hunk if any
    if current_diff is not None and hunk_lines and hunk_header is not None:
        current_diff.hunks.append(Hunk(*hunk_header, hunk_lines))

    return diffs