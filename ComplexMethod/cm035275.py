def parse_patch(text: str | list[str]) -> Iterable[diffobj]:
    lines = text.splitlines() if isinstance(text, str) else text

    # maybe use this to nuke all of those line endings?
    # lines = [x.splitlines()[0] for x in lines]
    lines = [x if len(x) == 0 else x.splitlines()[0] for x in lines]

    check = [
        unified_header_index,
        diffcmd_header,
        cvs_header_rcs,
        git_header_index,
        context_header_old_line,
        unified_header_old_line,
    ]

    diffs = []
    for c in check:
        diffs = split_by_regex(lines, c)
        if len(diffs) > 1:
            break

    for diff in diffs:
        difftext = '\n'.join(diff) + '\n'
        h = parse_header(diff)
        d = parse_diff(diff)
        if h or d:
            yield diffobj(header=h, changes=d, text=difftext)