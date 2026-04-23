def parse_default_diff(text: str | list[str]) -> list[Change] | None:
    lines = text.splitlines() if isinstance(text, str) else text

    old = 0
    new = 0
    old_len = 0
    new_len = 0
    r = 0
    i = 0

    changes = list()

    hunks = split_by_regex(lines, default_hunk_start)
    for hunk_n, hunk in enumerate(hunks):
        if not len(hunk):
            continue

        r = 0
        i = 0
        while len(hunk) > 0:
            h = default_hunk_start.match(hunk[0])
            c = default_change.match(hunk[0])
            del hunk[0]
            if h:
                old = int(h.group(1))
                if len(h.group(2)) > 0:
                    old_len = int(h.group(2)) - old + 1
                else:
                    old_len = 0

                new = int(h.group(4))
                if len(h.group(5)) > 0:
                    new_len = int(h.group(5)) - new + 1
                else:
                    new_len = 0

            elif c:
                kind = c.group(1)
                line = c.group(2)

                if kind == '<' and (r != old_len or r == 0):
                    changes.append(Change(old + r, None, line, hunk_n))
                    r += 1
                elif kind == '>' and (i != new_len or i == 0):
                    changes.append(Change(None, new + i, line, hunk_n))
                    i += 1

    if len(changes) > 0:
        return changes

    return None