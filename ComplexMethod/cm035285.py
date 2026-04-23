def parse_ed_diff(text: str | list[str]) -> list[Change] | None:
    lines = text.splitlines() if isinstance(text, str) else text

    old = 0
    j = 0
    k = 0

    r = 0
    i = 0

    changes = list()

    hunks = split_by_regex(lines, ed_hunk_start)
    hunks.reverse()
    for hunk_n, hunk in enumerate(hunks):
        if not len(hunk):
            continue
        j = 0
        k = 0
        while len(hunk) > 0:
            o = ed_hunk_start.match(hunk[0])
            del hunk[0]

            if not o:
                continue

            old = int(o.group(1))
            old_end = int(o.group(2)) if len(o.group(2)) else old

            hunk_kind = o.group(3)
            if hunk_kind == 'd':
                k = 0
                while old_end >= old:
                    changes.append(Change(old + k, None, None, hunk_n))
                    r += 1
                    k += 1
                    old_end -= 1
                continue

            while len(hunk) > 0:
                e = ed_hunk_end.match(hunk[0])
                if not e and hunk_kind == 'c':
                    k = 0
                    while old_end >= old:
                        changes.append(Change(old + k, None, None, hunk_n))
                        r += 1
                        k += 1
                        old_end -= 1

                    # I basically have no idea why this works
                    # for these tests.
                    changes.append(
                        Change(
                            None,
                            old - r + i + k + j,
                            hunk[0],
                            hunk_n,
                        )
                    )
                    i += 1
                    j += 1
                if not e and hunk_kind == 'a':
                    changes.append(
                        Change(
                            None,
                            old - r + i + 1,
                            hunk[0],
                            hunk_n,
                        )
                    )
                    i += 1

                del hunk[0]

    if len(changes) > 0:
        return changes

    return None