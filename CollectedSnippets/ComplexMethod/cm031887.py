def _fmt_line(parsed, data=None):
    parts = [
        f'<{parsed.kind.value}>',
    ]
    parent = ''
    if parsed.parent:
        parent = parsed.parent
        if not isinstance(parent, str):
            if parent.kind is KIND.FUNCTION:
                parent = f'{parent.name}()'
            else:
                parent = parent.name
        name = f'<{parent}>.{parsed.name}'
    else:
        name = parsed.name
    if data is None:
        data = parsed.data
    elif data is iter(data):
        data, = data
    parts.extend([
        name,
        f'<{data}>' if data else '-',
        f'({str(parsed.file or "<unknown file>")})',
    ])
    yield '\t'.join(parts)