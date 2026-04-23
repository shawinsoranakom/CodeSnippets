def _iter_lines(text, reqfile, samefiles, cwd, raw=False):
    lines = iter(text.splitlines())

    # The first line is special.
    # The subsequent lines are consistent.
    firstlines = [
        f'# 1 "{reqfile}"',
        '# 1 "<built-in>" 1',
        '# 1 "<built-in>" 3',
        '# 370 "<built-in>" 3',
        '# 1 "<command line>" 1',
        '# 1 "<built-in>" 2',
    ]
    for expected in firstlines:
        line = next(lines)
        if line != expected:
            raise NotImplementedError((line, expected))

    # Do all the CLI-provided includes.
    filter_reqfile = (lambda f: _gcc._filter_reqfile(f, reqfile, samefiles))
    make_info = (lambda lno: _common.FileInfo(reqfile, lno))
    last = None
    for line in lines:
        assert last != reqfile, (last,)
        # NOTE:condition is clang specific
        if not line:
            continue
        lno, included, flags = _gcc._parse_marker_line(line, reqfile)
        if not included:
            raise NotImplementedError((line,))
        if included == reqfile:
            # This will be the last one.
            assert 2 in flags, (line, flags)
        else:
            # NOTE:first condition is specific to clang
            if _normpath(included, cwd) == reqfile:
                assert 1 in flags or 2 in flags, (line, flags, included, reqfile)
            else:
                assert 1 in flags, (line, flags, included, reqfile)
        yield from _gcc._iter_top_include_lines(
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
    # NOTE:_normpath is clang specific
    assert _normpath(included, cwd) == reqfile, (line,)