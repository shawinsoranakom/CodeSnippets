def _parse_line(line):
    m = re.match(REGEX, line)
    if not m:
        return None
    (static, extern, capi,
     name,
     def_, decl,
     excname,
     ) = m.groups()
    if def_:
        isdecl = False
        if extern or capi:
            raise NotImplementedError(line)
        kind = 'static' if static else None
    elif excname:
        name = f'_PyExc_{excname}'
        isdecl = False
        kind = 'static'
    else:
        isdecl = True
        if static:
            kind = 'static'
        elif extern:
            kind = 'extern'
        elif capi:
            kind = 'capi'
        else:
            kind = None
    return name, isdecl, kind