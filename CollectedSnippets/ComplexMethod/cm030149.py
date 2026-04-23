def find_function(funcname, filename):
    cre = re.compile(r'(?:async\s+)?def\s+%s(\s*\[.+\])?\s*[(]' % re.escape(funcname))
    try:
        fp = tokenize.open(filename)
    except OSError:
        lines = linecache.getlines(filename)
        if not lines:
            return None
        fp = io.StringIO(''.join(lines))
    funcdef = ""
    funcstart = 0
    # consumer of this info expects the first line to be 1
    with fp:
        for lineno, line in enumerate(fp, start=1):
            if cre.match(line):
                funcstart, funcdef = lineno, line
            elif funcdef:
                funcdef += line

            if funcdef:
                try:
                    code = compile(funcdef, filename, 'exec')
                except SyntaxError:
                    continue
                # We should always be able to find the code object here
                funccode = next(c for c in code.co_consts if
                                isinstance(c, CodeType) and c.co_name == funcname)
                lineno_offset = find_first_executable_line(funccode)
                return funcname, filename, funcstart + lineno_offset - 1
    return None