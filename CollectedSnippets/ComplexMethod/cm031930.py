def summarize(items, *, groupby='kind', includeempty=True, minimize=None):
    if minimize is None:
        if includeempty is None:
            minimize = True
            includeempty = False
        else:
            minimize = includeempty
    elif includeempty is None:
        includeempty = minimize
    elif minimize and includeempty:
        raise ValueError(f'cannot minimize and includeempty at the same time')

    groupby = _parse_groupby(groupby)[0]
    _outer, _inner = _resolve_full_groupby(groupby)
    outers = GROUPINGS[_outer]
    inners = GROUPINGS[_inner]

    summary = {
        'totals': {
            'all': 0,
            'subs': {o: 0 for o in outers},
            'bygroup': {o: {i: 0 for i in inners}
                        for o in outers},
        },
    }

    for item in items:
        outer = getattr(item, _outer)
        inner = getattr(item, _inner)
        # Update totals.
        summary['totals']['all'] += 1
        summary['totals']['subs'][outer] += 1
        summary['totals']['bygroup'][outer][inner] += 1

    if not includeempty:
        subtotals = summary['totals']['subs']
        bygroup = summary['totals']['bygroup']
        for outer in outers:
            if subtotals[outer] == 0:
                del subtotals[outer]
                del bygroup[outer]
                continue

            for inner in inners:
                if bygroup[outer][inner] == 0:
                    del bygroup[outer][inner]
            if minimize:
                if len(bygroup[outer]) == 1:
                    del bygroup[outer]

    return summary