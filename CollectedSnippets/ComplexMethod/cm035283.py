def parse_unified_diff(text: str | list[str]) -> list[Change] | None:
    lines = text.splitlines() if isinstance(text, str) else text

    old = 0
    new = 0
    r = 0
    i = 0
    old_len = 0
    new_len = 0

    changes = list()

    hunks = split_by_regex(lines, unified_hunk_start)
    for hunk_n, hunk in enumerate(hunks):
        # reset counters
        r = 0
        i = 0
        while len(hunk) > 0:
            h = unified_hunk_start.match(hunk[0])
            del hunk[0]
            if h:
                # The hunk header @@ -1,6 +1,6 @@ means:
                # - Start at line 1 in the old file and show 6 lines
                # - Start at line 1 in the new file and show 6 lines
                old = int(h.group(1))  # Starting line in old file
                old_len = (
                    int(h.group(2)) if len(h.group(2)) > 0 else 1
                )  # Number of lines in old file

                new = int(h.group(3))  # Starting line in new file
                new_len = (
                    int(h.group(4)) if len(h.group(4)) > 0 else 1
                )  # Number of lines in new file

                h = None
                break

        # Process each line in the hunk
        for n in hunk:
            # Each line in a unified diff starts with a space (context), + (addition), or - (deletion)
            # The first character is the kind, the rest is the line content
            kind = (
                n[0] if len(n) > 0 else ' '
            )  # Empty lines in the hunk are treated as context lines
            line = n[1:] if len(n) > 1 else ''

            # Process the line based on its kind
            if kind == '-' and (r != old_len or r == 0):
                # Line was removed from the old file
                changes.append(Change(old + r, None, line, hunk_n))
                r += 1
            elif kind == '+' and (i != new_len or i == 0):
                # Line was added in the new file
                changes.append(Change(None, new + i, line, hunk_n))
                i += 1
            elif kind == ' ':
                # Context line - exists in both old and new file
                changes.append(Change(old + r, new + i, line, hunk_n))
                r += 1
                i += 1

    if len(changes) > 0:
        return changes

    return None