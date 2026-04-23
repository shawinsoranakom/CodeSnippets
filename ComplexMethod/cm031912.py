def _strip_directives(line, partial=0):
    # We assume there are no string literals with parens in directive bodies.
    while partial > 0:
        if not (m := re.match(r'[^{}]*([()])', line)):
            return None, partial
        delim, = m.groups()
        partial += 1 if delim == '(' else -1  # opened/closed
        line = line[m.end():]

    line = re.sub(r'__extension__', '', line)
    line = re.sub(r'__thread\b', '_Thread_local', line)

    while (m := COMPILER_DIRECTIVE_RE.match(line)):
        before, _, _, closed = m.groups()
        if closed:
            line = f'{before} {line[m.end():]}'
        else:
            after, partial = _strip_directives(line[m.end():], 2)
            line = f'{before} {after or ""}'
            if partial:
                break

    return line, partial