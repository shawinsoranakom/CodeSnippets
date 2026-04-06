def _get_between(content, start, end=None):
    should_yield = False
    for line in content.split('\n'):
        if start in line:
            should_yield = True
            continue

        if end and end in line:
            return

        if should_yield and line:
            yield line.strip().split(' ')[0]