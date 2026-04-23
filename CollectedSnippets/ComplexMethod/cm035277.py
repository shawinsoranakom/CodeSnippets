def parse_git_header(text: str | list[str]) -> header | None:
    lines = text.splitlines() if isinstance(text, str) else text

    old_version = None
    new_version = None
    old_path = None
    new_path = None
    cmd_old_path = None
    cmd_new_path = None
    for line in lines:
        hm = git_diffcmd_header.match(line)
        if hm:
            cmd_old_path = hm.group(1)
            cmd_new_path = hm.group(2)
            continue

        g = git_header_index.match(line)
        if g:
            old_version = g.group(1)
            new_version = g.group(2)
            continue

        # git always has its own special headers
        o = git_header_old_line.match(line)
        if o:
            old_path = o.group(1)

        n = git_header_new_line.match(line)
        if n:
            new_path = n.group(1)

        binary = git_header_binary_file.match(line)
        if binary:
            old_path = binary.group(1)
            new_path = binary.group(2)

        if old_path and new_path:
            if old_path.startswith('a/'):
                old_path = old_path[2:]

            if new_path.startswith('b/'):
                new_path = new_path[2:]
            return header(
                index_path=None,
                old_path=old_path,
                old_version=old_version,
                new_path=new_path,
                new_version=new_version,
            )

    # if we go through all of the text without finding our normal info,
    # use the cmd if available
    if cmd_old_path and cmd_new_path and old_version and new_version:
        if cmd_old_path.startswith('a/'):
            cmd_old_path = cmd_old_path[2:]

        if cmd_new_path.startswith('b/'):
            cmd_new_path = cmd_new_path[2:]

        return header(
            index_path=None,
            # wow, I kind of hate this:
            # assume /dev/null if the versions are zeroed out
            old_path='/dev/null' if old_version == '0000000' else cmd_old_path,
            old_version=old_version,
            new_path='/dev/null' if new_version == '0000000' else cmd_new_path,
            new_version=new_version,
        )

    return None