def parse_cvs_header(text: str | list[str]) -> header | None:
    lines = text.splitlines() if isinstance(text, str) else text

    headers = findall_regex(lines, cvs_header_rcs)
    headers_old = findall_regex(lines, old_cvs_diffcmd_header)

    if headers:
        # parse rcs style headers
        while len(lines) > 0:
            i = cvs_header_index.match(lines[0])
            del lines[0]
            if not i:
                continue

            diff_header = parse_diff_header(lines)
            if diff_header:
                over = diff_header.old_version
                if over:
                    oend = cvs_header_timestamp.match(over)
                    oend_c = cvs_header_timestamp_colon.match(over)
                    if oend:
                        over = oend.group(2)
                    elif oend_c:
                        over = oend_c.group(1)

                nver = diff_header.new_version
                if nver:
                    nend = cvs_header_timestamp.match(nver)
                    nend_c = cvs_header_timestamp_colon.match(nver)
                    if nend:
                        nver = nend.group(2)
                    elif nend_c:
                        nver = nend_c.group(1)

                return header(
                    index_path=i.group(1),
                    old_path=diff_header.old_path,
                    old_version=over,
                    new_path=diff_header.new_path,
                    new_version=nver,
                )
            return header(
                index_path=i.group(1),
                old_path=i.group(1),
                old_version=None,
                new_path=i.group(1),
                new_version=None,
            )
    elif headers_old:
        # parse old style headers
        while len(lines) > 0:
            i = cvs_header_index.match(lines[0])
            del lines[0]
            if not i:
                continue

            d = old_cvs_diffcmd_header.match(lines[0])
            if not d:
                return header(
                    index_path=i.group(1),
                    old_path=i.group(1),
                    old_version=None,
                    new_path=i.group(1),
                    new_version=None,
                )

            # will get rid of the useless stuff for us
            parse_diff_header(lines)
            over = d.group(2) if d.group(2) else None
            nver = d.group(4) if d.group(4) else None
            return header(
                index_path=i.group(1),
                old_path=d.group(1),
                old_version=over,
                new_path=d.group(3),
                new_version=nver,
            )

    return None