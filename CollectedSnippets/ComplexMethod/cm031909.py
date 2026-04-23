def _iter_lines(text, reqfile, samefiles, cwd, raw=False):
    lines = iter(text.splitlines())

    # The first line is special.
    # The next two lines are consistent.
    firstlines = [
        f'# 0 "{reqfile}"',
        '# 0 "<built-in>"',
        '# 0 "<command-line>"',
    ]
    if text.startswith('# 1 '):
        # Some preprocessors emit a lineno of 1 for line-less entries.
        firstlines = [l.replace('# 0 ', '# 1 ') for l in firstlines]
    for expected in firstlines:
        line = next(lines)
        if line != expected:
            raise NotImplementedError((line, expected))

    # Do all the CLI-provided includes.
    filter_reqfile = (lambda f: _filter_reqfile(f, reqfile, samefiles))
    make_info = (lambda lno: _common.FileInfo(reqfile, lno))
    last = None
    for line in lines:
        assert last != reqfile, (last,)
        lno, included, flags = _parse_marker_line(line, reqfile)
        if not included:
            raise NotImplementedError((line,))
        if included == reqfile:
            # This will be the last one.
            assert not flags, (line, flags)
        else:
            assert 1 in flags, (line, flags)
        yield from _iter_top_include_lines(
            lines,
            _normpath(included, cwd),
            cwd,
            filter_reqfile,
            make_info,
            raw,
            EXIT_MARKERS
        )
        last = included
    # The last one is always the requested file.
    assert included == reqfile, (line,)