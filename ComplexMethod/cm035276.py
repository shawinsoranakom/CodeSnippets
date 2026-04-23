def parse_scm_header(text: str | list[str]) -> header | None:
    lines = text.splitlines() if isinstance(text, str) else text

    check = [
        (git_header_index, parse_git_header),
        (old_cvs_diffcmd_header, parse_cvs_header),
        (cvs_header_rcs, parse_cvs_header),
        (svn_header_index, parse_svn_header),
    ]

    for regex, parser in check:
        diffs = findall_regex(lines, regex)
        if len(diffs) > 0:
            git_opt = findall_regex(lines, git_diffcmd_header)
            if len(git_opt) > 0:
                res = parser(lines)
                if res:
                    old_path = res.old_path
                    new_path = res.new_path
                    if old_path.startswith('a/'):
                        old_path = old_path[2:]

                    if new_path.startswith('b/'):
                        new_path = new_path[2:]

                    return header(
                        index_path=res.index_path,
                        old_path=old_path,
                        old_version=res.old_version,
                        new_path=new_path,
                        new_version=res.new_version,
                    )
            else:
                res = parser(lines)

            return res

    return None