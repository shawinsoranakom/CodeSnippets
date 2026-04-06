def _search(output):
    for pattern in patterns:
        m = pattern(output)
        if m and os.path.isfile(m.group('file')):
            return m