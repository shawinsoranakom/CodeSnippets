def parse_git_binary_diff(text: str | list[str]) -> list[Change] | None:
    lines = text.splitlines() if isinstance(text, str) else text

    changes: list[Change] = list()

    old_version = None
    new_version = None
    cmd_old_path = None
    cmd_new_path = None
    # the sizes are used as latch-up
    new_size = 0
    old_size = 0
    old_encoded = ''
    new_encoded = ''
    for line in lines:
        if cmd_old_path is None and cmd_new_path is None:
            hm = git_diffcmd_header.match(line)
            if hm:
                cmd_old_path = hm.group(1)
                cmd_new_path = hm.group(2)
                continue

        if old_version is None and new_version is None:
            g = git_header_index.match(line)
            if g:
                old_version = g.group(1)
                new_version = g.group(2)
                continue

        # the first is added file
        if new_size == 0:
            literal = git_binary_literal_start.match(line)
            if literal:
                new_size = int(literal.group(1))
                continue
            delta = git_binary_delta_start.match(line)
            if delta:
                # not supported
                new_size = 0
                continue
        elif new_size > 0:
            if base85string.match(line):
                assert len(line) >= 6 and ((len(line) - 1) % 5) == 0
                new_encoded += line[1:]
            elif 0 == len(line):
                if new_encoded:
                    decoded = base64.b85decode(new_encoded)
                    added_data = zlib.decompress(decoded)
                    assert new_size == len(added_data)
                    change = Change(None, 0, added_data, None)
                    changes.append(change)
                new_size = 0
                new_encoded = ''
            else:
                # Invalid line format
                new_size = 0
                new_encoded = ''

        # the second is removed file
        if old_size == 0:
            literal = git_binary_literal_start.match(line)
            if literal:
                old_size = int(literal.group(1))
            delta = git_binary_delta_start.match(line)
            if delta:
                # not supported
                old_size = 0
                continue
        elif old_size > 0:
            if base85string.match(line):
                assert len(line) >= 6 and ((len(line) - 1) % 5) == 0
                old_encoded += line[1:]
            elif 0 == len(line):
                if old_encoded:
                    decoded = base64.b85decode(old_encoded)
                    removed_data = zlib.decompress(decoded)
                    assert old_size == len(removed_data)
                    change = Change(0, None, None, removed_data)
                    changes.append(change)
                old_size = 0
                old_encoded = ''
            else:
                # Invalid line format
                old_size = 0
                old_encoded = ''

    return changes