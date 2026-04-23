def parse_svn_header(text: str | list[str]) -> header | None:
    lines = text.splitlines() if isinstance(text, str) else text

    headers = findall_regex(lines, svn_header_index)
    if len(headers) == 0:
        return None

    while len(lines) > 0:
        i = svn_header_index.match(lines[0])
        del lines[0]
        if not i:
            continue

        diff_header = parse_diff_header(lines)
        if not diff_header:
            return header(
                index_path=i.group(1),
                old_path=i.group(1),
                old_version=None,
                new_path=i.group(1),
                new_version=None,
            )

        opath = diff_header.old_path
        over = diff_header.old_version
        if over:
            oend = svn_header_timestamp_version.match(over)
            if oend and oend.group(1):
                over = int(oend.group(1))
        elif opath:
            ts = svn_header_timestamp.match(opath)
            if ts:
                opath = opath[: -len(ts.group(1))]
                oend = svn_header_timestamp_version.match(ts.group(1))
                if oend and oend.group(1):
                    over = int(oend.group(1))

        npath = diff_header.new_path
        nver = diff_header.new_version
        if nver:
            nend = svn_header_timestamp_version.match(diff_header.new_version)
            if nend and nend.group(1):
                nver = int(nend.group(1))
        elif npath:
            ts = svn_header_timestamp.match(npath)
            if ts:
                npath = npath[: -len(ts.group(1))]
                nend = svn_header_timestamp_version.match(ts.group(1))
                if nend and nend.group(1):
                    nver = int(nend.group(1))

        if not isinstance(over, int):
            over = None

        if not isinstance(nver, int):
            nver = None

        return header(
            index_path=i.group(1),
            old_path=opath,
            old_version=over,
            new_path=npath,
            new_version=nver,
        )

    return None