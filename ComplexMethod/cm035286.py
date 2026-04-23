def parse_rcs_ed_diff(text: str | list[str]) -> list[Change] | None:
    # much like forward ed, but no 'c' type
    lines = text.splitlines() if isinstance(text, str) else text

    old = 0
    j = 0
    size = 0
    total_change_size = 0

    changes = list()

    hunks = split_by_regex(lines, rcs_ed_hunk_start)
    for hunk_n, hunk in enumerate(hunks):
        if len(hunk):
            j = 0
            while len(hunk) > 0:
                o = rcs_ed_hunk_start.match(hunk[0])
                del hunk[0]

                if not o:
                    continue

                hunk_kind = o.group(1)
                old = int(o.group(2))
                size = int(o.group(3)) if o.group(3) else 0

                if hunk_kind == 'a':
                    old += total_change_size + 1
                    total_change_size += size
                    while size > 0 and len(hunk) > 0:
                        changes.append(Change(None, old + j, hunk[0], hunk_n))
                        j += 1
                        size -= 1

                        del hunk[0]

                elif hunk_kind == 'd':
                    total_change_size -= size
                    while size > 0:
                        changes.append(Change(old + j, None, None, hunk_n))
                        j += 1
                        size -= 1

    if len(changes) > 0:
        return changes
    return None