def _parse_commands(lines, starts_with):
    lines = dropwhile(lambda line: not line.startswith(starts_with), lines)
    lines = islice(lines, 1, None)
    lines = list(takewhile(lambda line: line.strip(), lines))
    return [line.strip().split(' ')[0] for line in lines]