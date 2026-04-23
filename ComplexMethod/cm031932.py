def render_table(items, *,
                 columns=None,
                 groupby='kind',
                 sort=True,
                 showempty=False,
                 verbose=False,
                 ):
    if groupby is None:
        groupby = 'kind'
    if showempty is None:
        showempty = False

    if groupby:
        (collated, groupby, maxfilename, maxname, maxextra,
         ) = _collate(items, groupby, showempty)
        for grouping in GROUPINGS:
            maxextra[grouping] = max(len(g) for g in GROUPINGS[grouping])

        _, extra = _resolve_full_groupby(groupby)
        extras = [extra]
        markers = {extra: _MARKERS[extra]}

        groups = GROUPINGS[groupby]
    else:
        # XXX Support no grouping?
        raise NotImplementedError

    if columns:
        def get_extra(item):
            return {extra: getattr(item, extra)
                    for extra in ('kind', 'level')}
    else:
        if verbose:
            extracols = [f'{extra}:{maxextra[extra]}'
                         for extra in extras]
            def get_extra(item):
                return {extra: getattr(item, extra)
                        for extra in extras}
        elif len(extras) == 1:
            extra, = extras
            extracols = [f'{m}:1' for m in markers[extra]]
            def get_extra(item):
                return {m: m if getattr(item, extra) == markers[extra][m] else ''
                        for m in markers[extra]}
        else:
            raise NotImplementedError
            #extracols = [[f'{m}:1' for m in markers[extra]]
            #             for extra in extras]
            #def get_extra(item):
            #    values = {}
            #    for extra in extras:
            #        cur = markers[extra]
            #        for m in cur:
            #            values[m] = m if getattr(item, m) == cur[m] else ''
            #    return values
        columns = [
            f'filename:{maxfilename}',
            f'name:{maxname}',
            *extracols,
        ]
    header, div, fmt = build_table(columns)

    if sort:
        sortkey = _get_sortkey(sort, groupby, columns)

    total = 0
    for group, grouped in collated.items():
        if not showempty and group not in collated:
            continue
        yield ''
        yield f' === {group} ==='
        yield ''
        yield header
        yield div
        if grouped:
            if sort:
                grouped = sorted(grouped, key=sortkey)
            for item in grouped:
                yield fmt.format(
                    filename=item.relfile,
                    name=item.name,
                    **get_extra(item),
                )
        yield div
        subtotal = len(grouped)
        yield f'  sub-total: {subtotal}'
        total += subtotal
    yield ''
    yield f'total: {total}'