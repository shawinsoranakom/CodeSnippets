def filter_by_kind(items, kind):
    if kind == 'type':
        kinds = _KIND._TYPE_DECLS
    elif kind == 'decl':
        kinds = _KIND._TYPE_DECLS
    try:
        okay = kind in _KIND
    except TypeError:
        kinds = set(kind)
    else:
        kinds = {kind} if okay else set(kind)
    for item in items:
        if item.kind in kinds:
            yield item