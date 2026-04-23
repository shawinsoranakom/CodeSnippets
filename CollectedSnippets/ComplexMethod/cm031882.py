def fmt_summary(filename, item, *, showfwd=None):
    if item.filename != filename:
        yield f'> {item.filename}'

    if showfwd is None:
        LINE = ' {lno:>5} {kind:10} {funcname:40} {fwd:1} {name:40} {data}'
    else:
        LINE = ' {lno:>5} {kind:10} {funcname:40} {name:40} {data}'
    lno = kind = funcname = fwd = name = data = ''
    MIN_LINE = len(LINE.format(**locals()))

    fileinfo, kind, funcname, name, data = item
    lno = fileinfo.lno if fileinfo and fileinfo.lno >= 0 else ''
    funcname = funcname or ' --'
    name = name or ' --'
    isforward = False
    if kind is KIND.FUNCTION:
        storage, inline, params, returntype, isforward = data.values()
        returntype = _format_vartype(returntype)
        data = returntype + params
        if inline:
            data = f'inline {data}'
        if storage:
            data = f'{storage} {data}'
    elif kind is KIND.VARIABLE:
        data = _format_vartype(data)
    elif kind is KIND.STRUCT or kind is KIND.UNION:
        if data is None:
            isforward = True
        else:
            fields = data
            data = f'({len(data)}) {{ '
            indent = ',\n' + ' ' * (MIN_LINE + len(data))
            data += ', '.join(f.name for f in fields[:5])
            fields = fields[5:]
            while fields:
                data = f'{data}{indent}{", ".join(f.name for f in fields[:5])}'
                fields = fields[5:]
            data += ' }'
    elif kind is KIND.ENUM:
        if data is None:
            isforward = True
        else:
            names = [d if isinstance(d, str) else d.name
                     for d in data]
            data = f'({len(data)}) {{ '
            indent = ',\n' + ' ' * (MIN_LINE + len(data))
            data += ', '.join(names[:5])
            names = names[5:]
            while names:
                data = f'{data}{indent}{", ".join(names[:5])}'
                names = names[5:]
            data += ' }'
    elif kind is KIND.TYPEDEF:
        data = f'typedef {data}'
    elif kind == KIND.STATEMENT:
        pass
    else:
        raise NotImplementedError(item)
    if isforward:
        fwd = '*'
        if not showfwd and showfwd is not None:
            return
    elif showfwd:
        return
    kind = kind.value
    yield LINE.format(**locals())