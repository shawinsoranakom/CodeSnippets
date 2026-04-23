def normalize_selection(selected: str, *, possible=None):
    if selected in (None, True, False):
        return selected
    elif isinstance(selected, str):
        selected = [selected]
    elif not selected:
        return ()

    unsupported = []
    _selected = set()
    for item in selected:
        if not item:
            continue
        for value in item.strip().replace(',', ' ').split():
            if not value:
                continue
            # XXX Handle subtraction (leading "-").
            if possible and value not in possible and value != 'all':
                unsupported.append(value)
            _selected.add(value)
    if unsupported:
        raise UnsupportedSelectionError(unsupported, tuple(possible))
    if 'all' in _selected:
        return True
    return frozenset(selected)