def _iter_top_include_lines(lines, topfile, cwd,
                            filter_reqfile, make_info,
                            raw, exit_markers):
    partial = 0  # depth
    files = [topfile]
    # We start at 1 in case there are source lines (including blank ones)
    # before the first marker line.  Also, we already verified in
    # _parse_marker_line() that the preprocessor reported lno as 1.
    lno = 1
    for line in lines:
        if line in exit_markers:
            # We're done with this top-level include.
            return

        _lno, included, flags = _parse_marker_line(line)
        if included:
            # HACK:
            # Mixes curses.h and ncurses.h marker lines
            # gcc silently passes this, while clang fails
            # See: /Include/py_curses.h #if-elif directives
            # And compare with preprocessor output
            if os.path.basename(included) == 'curses.h':
                included = os.path.join(os.path.dirname(included), 'ncurses.h')

            lno = _lno
            included = _normpath(included, cwd)
            # We hit a marker line.
            if 1 in flags:
                # We're entering a file.
                # XXX Cycles are unexpected?
                #assert included not in files, (line, files)
                files.append(included)
            elif 2 in flags:
                # We're returning to a file.
                assert files and included in files, (line, files)
                assert included != files[-1], (line, files)
                while files[-1] != included:
                    files.pop()
                # XXX How can a file return to line 1?
                #assert lno > 1, (line, lno)
            else:
                if included == files[-1]:
                    # It's the next line from the file.
                    assert lno > 1, (line, lno)
                else:
                    # We ran into a user-added #LINE directive,
                    # which we promptly ignore.
                    pass
        elif not files:
            raise NotImplementedError((line,))
        elif filter_reqfile(files[-1]):
            assert lno is not None, (line, files[-1])
            if (m := PREPROC_DIRECTIVE_RE.match(line)):
                name, = m.groups()
                if name != 'pragma':
                    raise Exception(line)
            else:
                line = re.sub(r'__inline__', 'inline', line)
                if not raw:
                    line, partial = _strip_directives(line, partial=partial)
                yield _common.SourceLine(
                    make_info(lno),
                    'source',
                    line or '',
                    None,
                )
            lno += 1