def parse_context_diff(text: str | list[str]) -> list[Change] | None:
    lines = text.splitlines() if isinstance(text, str) else text

    old = 0
    new = 0
    j = 0
    k = 0

    changes = list()

    hunks = split_by_regex(lines, context_hunk_start)
    for hunk_n, hunk in enumerate(hunks):
        if not len(hunk):
            continue

        j = 0
        k = 0
        parts = split_by_regex(hunk, context_hunk_new)
        if len(parts) != 2:
            raise exceptions.ParseException('Context diff invalid', hunk_n)

        old_hunk = parts[0]
        new_hunk = parts[1]

        while len(old_hunk) > 0:
            o = context_hunk_old.match(old_hunk[0])
            del old_hunk[0]

            if not o:
                continue

            old = int(o.group(1))
            old_len = int(o.group(2)) + 1 - old
            while len(new_hunk) > 0:
                n = context_hunk_new.match(new_hunk[0])
                del new_hunk[0]

                if not n:
                    continue

                new = int(n.group(1))
                new_len = int(n.group(2)) + 1 - new
                break
            break

        # now have old and new set, can start processing?
        if len(old_hunk) > 0 and len(new_hunk) == 0:
            msg = 'Got unexpected change in removal hunk: '
            # only removes left?
            while len(old_hunk) > 0:
                c = context_change.match(old_hunk[0])
                del old_hunk[0]

                if not c:
                    continue

                kind = c.group(1)
                line = c.group(2)

                if kind == '-' and (j != old_len or j == 0):
                    changes.append(Change(old + j, None, line, hunk_n))
                    j += 1
                elif kind == ' ' and (
                    (j != old_len and k != new_len) or (j == 0 or k == 0)
                ):
                    changes.append(Change(old + j, new + k, line, hunk_n))
                    j += 1
                    k += 1
                elif kind == '+' or kind == '!':
                    raise exceptions.ParseException(msg + kind, hunk_n)

            continue

        if len(old_hunk) == 0 and len(new_hunk) > 0:
            msg = 'Got unexpected change in removal hunk: '
            # only insertions left?
            while len(new_hunk) > 0:
                c = context_change.match(new_hunk[0])
                del new_hunk[0]

                if not c:
                    continue

                kind = c.group(1)
                line = c.group(2)

                if kind == '+' and (k != new_len or k == 0):
                    changes.append(Change(None, new + k, line, hunk_n))
                    k += 1
                elif kind == ' ' and (
                    (j != old_len and k != new_len) or (j == 0 or k == 0)
                ):
                    changes.append(Change(old + j, new + k, line, hunk_n))
                    j += 1
                    k += 1
                elif kind == '-' or kind == '!':
                    raise exceptions.ParseException(msg + kind, hunk_n)
            continue

        # both
        while len(old_hunk) > 0 and len(new_hunk) > 0:
            oc = context_change.match(old_hunk[0])
            nc = context_change.match(new_hunk[0])
            okind = None
            nkind = None

            if oc:
                okind = oc.group(1)
                oline = oc.group(2)

            if nc:
                nkind = nc.group(1)
                nline = nc.group(2)

            if not (oc or nc):
                del old_hunk[0]
                del new_hunk[0]
            elif okind == ' ' and nkind == ' ' and oline == nline:
                changes.append(Change(old + j, new + k, oline, hunk_n))
                j += 1
                k += 1
                del old_hunk[0]
                del new_hunk[0]
            elif okind == '-' or okind == '!' and (j != old_len or j == 0):
                changes.append(Change(old + j, None, oline, hunk_n))
                j += 1
                del old_hunk[0]
            elif nkind == '+' or nkind == '!' and (k != new_len or k == 0):
                changes.append(Change(None, new + k, nline, hunk_n))
                k += 1
                del new_hunk[0]
            else:
                return None

    if len(changes) > 0:
        return changes

    return None