def render_full(items, *,
                groupby='kind',
                sort=None,
                showempty=None,
                verbose=False,
                ):
    if groupby is None:
        groupby = 'kind'
    if showempty is None:
        showempty = False

    if sort:
        sortkey = _get_sortkey(sort, groupby, None)

    if groupby:
        collated, groupby, _, _, _ = _collate(items, groupby, showempty)
        for group, grouped in collated.items():
            yield '#' * 25
            yield f'# {group} ({len(grouped)})'
            yield '#' * 25
            yield ''
            if not grouped:
                continue
            if sort:
                grouped = sorted(grouped, key=sortkey)
            for item in grouped:
                yield from _render_item_full(item, groupby, verbose)
                yield ''
    else:
        if sort:
            items = sorted(items, key=sortkey)
        for item in items:
            yield from _render_item_full(item, None, verbose)
            yield ''