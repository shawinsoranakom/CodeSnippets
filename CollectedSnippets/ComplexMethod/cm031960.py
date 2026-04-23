def fix_row(row, **markers):
    if isinstance(row, str):
        raise NotImplementedError(row)
    empty = parse_markers(markers.pop('empty', ('-',)))
    unknown = parse_markers(markers.pop('unknown', ('???',)))
    row = (val if val else None for val in row)
    if not empty:
        if unknown:
            row = (UNKNOWN if val in unknown else val for val in row)
    elif not unknown:
        row = (EMPTY if val in empty else val for val in row)
    else:
        row = (EMPTY if val in empty else (UNKNOWN if val in unknown else val)
               for val in row)
    return tuple(row)