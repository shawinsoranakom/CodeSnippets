def _fmt_full(parsed, data=None):
    if parsed.kind is KIND.VARIABLE and parsed.parent:
        prefix = 'local '
        suffix = f' ({parsed.parent.name})'
    else:
        # XXX Show other prefixes (e.g. global, public)
        prefix = suffix = ''
    yield f'{prefix}{parsed.kind.value} {parsed.name!r}{suffix}'
    for column, info in parsed.render_rowdata().items():
        if column == 'kind':
            continue
        if column == 'name':
            continue
        if column == 'parent' and parsed.kind is not KIND.VARIABLE:
            continue
        if column == 'data':
            if parsed.kind in (KIND.STRUCT, KIND.UNION):
                column = 'members'
            elif parsed.kind is KIND.ENUM:
                column = 'enumerators'
            elif parsed.kind is KIND.STATEMENT:
                column = 'text'
                data, = data
            else:
                column = 'signature'
                data, = data
            if not data:
#                yield f'\t{column}:\t-'
                continue
            elif isinstance(data, str):
                yield f'\t{column}:\t{data!r}'
            else:
                yield f'\t{column}:'
                for line in data:
                    yield f'\t\t- {line}'
        else:
            yield f'\t{column}:\t{info}'