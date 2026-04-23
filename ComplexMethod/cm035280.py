def parse_unified_header(text: str | list[str]) -> header | None:
    lines = text.splitlines() if isinstance(text, str) else text

    headers = findall_regex(lines, unified_header_new_line)
    if len(headers) == 0:
        return None

    while len(lines) > 1:
        o = unified_header_old_line.match(lines[0])
        del lines[0]
        if o:
            n = unified_header_new_line.match(lines[0])
            del lines[0]
            if n:
                over = o.group(2)
                if len(over) == 0:
                    over = None

                nver = n.group(2)
                if len(nver) == 0:
                    nver = None

                return header(
                    index_path=None,
                    old_path=o.group(1),
                    old_version=over,
                    new_path=n.group(1),
                    new_version=nver,
                )

    return None