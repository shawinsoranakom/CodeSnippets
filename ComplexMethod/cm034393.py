def parse_output_for_keys(output, short_format=False):

    found = []
    lines = to_native(output).split('\n')
    for line in lines:
        if (line.startswith("pub") or line.startswith("sub")) and "expired" not in line:
            try:
                # apt key format
                tokens = line.split()
                code = tokens[1]
                (len_type, real_code) = code.split("/")
            except (IndexError, ValueError):
                # gpg format
                try:
                    tokens = line.split(':')
                    real_code = tokens[4]
                except (IndexError, ValueError):
                    # invalid line, skip
                    continue
            found.append(real_code)

    if found and short_format:
        found = shorten_key_ids(found)

    return found