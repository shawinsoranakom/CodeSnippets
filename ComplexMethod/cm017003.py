def get_all_matched_commands(stderr, separator='Did you mean'):
    if not isinstance(separator, list):
        separator = [separator]
    should_yield = False
    for line in stderr.split('\n'):
        for sep in separator:
            if sep in line:
                should_yield = True
                break
        else:
            if should_yield and line:
                yield line.strip()