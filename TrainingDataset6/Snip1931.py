def _make_pattern(pattern):
    pattern = pattern.replace('{file}', '(?P<file>[^:\n]+)') \
                     .replace('{line}', '(?P<line>[0-9]+)') \
                     .replace('{col}', '(?P<col>[0-9]+)')
    return re.compile(pattern, re.MULTILINE)