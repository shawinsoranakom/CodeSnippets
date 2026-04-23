def _iter_source(lines, *, maxtext=11_000, maxlines=200, showtext=False):
    maxtext = maxtext if maxtext and maxtext > 0 else None
    maxlines = maxlines if maxlines and maxlines > 0 else None
    filestack = []
    allinfo = {}
    # "lines" should be (fileinfo, data), as produced by the preprocessor code.
    for fileinfo, line in lines:
        if fileinfo.filename in filestack:
            while fileinfo.filename != filestack[-1]:
                filename = filestack.pop()
                del allinfo[filename]
            filename = fileinfo.filename
            srcinfo = allinfo[filename]
        else:
            filename = fileinfo.filename
            srcinfo = SourceInfo(filename)
            filestack.append(filename)
            allinfo[filename] = srcinfo

        _logger.debug(f'-> {line}')
        srcinfo._add_line(line, fileinfo.lno)
        if srcinfo.too_much(maxtext, maxlines):
            break
        while srcinfo._used():
            yield srcinfo
            if showtext:
                _logger.debug(f'=> {srcinfo.text}')
    else:
        if not filestack:
            srcinfo = SourceInfo('???')
        else:
            filename = filestack[-1]
            srcinfo = allinfo[filename]
            while srcinfo._used():
                yield srcinfo
                if showtext:
                    _logger.debug(f'=> {srcinfo.text}')
        yield srcinfo
        if showtext:
            _logger.debug(f'=> {srcinfo.text}')
        if not srcinfo._ready:
            return
    # At this point either the file ended prematurely
    # or there's "too much" text.
    filename, lno_from, lno_to = srcinfo.filename, srcinfo.start, srcinfo.end
    text = srcinfo.text
    if len(text) > 500:
        text = text[:500] + '...'

    if srcinfo.too_much_text(maxtext):
        msg = f'''
            too much text, try to increase MAX_SIZES[MAXTEXT] in cpython/_parser.py
            {filename} starting at line {lno_from} to {lno_to}
            has code with length {len(srcinfo.text)} greater than {maxtext}:
            {text}
        '''
        raise RuntimeError(textwrap.dedent(msg))

    if srcinfo.too_many_lines(maxlines):
        msg = f'''
            too many lines, try to increase MAX_SIZES[MAXLINES] in cpython/_parser.py
            {filename} starting at line {lno_from} to {lno_to}
            has code with number of lines {lno_to - lno_from} greater than {maxlines}:
            {text}
        '''
        raise RuntimeError(textwrap.dedent(msg))

    raise RuntimeError(f'unmatched text ({filename} starting at line {lno_from}):\n{text}')