def _parse_marker_line(line, reqfile=None):
    m = LINE_MARKER_RE.match(line)
    if not m:
        return None, None, None
    lno, origfile, flags = m.groups()
    lno = int(lno)
    assert origfile not in META_FILES, (line,)
    assert lno > 0, (line, lno)
    flags = set(int(f) for f in flags.split()) if flags else ()

    if 1 in flags:
        # We're entering a file.
        assert lno == 1, (line, lno)
        assert 2 not in flags, (line,)
    elif 2 in flags:
        # We're returning to a file.
        #assert lno > 1, (line, lno)
        pass
    elif reqfile and origfile == reqfile:
        # We're starting the requested file.
        assert lno == 1, (line, lno)
        assert not flags, (line, flags)
    else:
        # It's the next line from the file.
        assert lno > 1, (line, lno)
    return lno, origfile, flags