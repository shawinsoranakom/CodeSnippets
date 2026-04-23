def render_summary(items, *,
                   groupby='kind',
                   sort=None,
                   showempty=None,
                   verbose=False,
                   ):
    if groupby is None:
        groupby = 'kind'
    summary = summarize(
        items,
        groupby=groupby,
        includeempty=showempty,
        minimize=None if showempty else not verbose,
    )

    subtotals = summary['totals']['subs']
    bygroup = summary['totals']['bygroup']
    for outer, subtotal in subtotals.items():
        if bygroup:
            subtotal = f'({subtotal})'
            yield f'{outer + ":":20} {subtotal:>8}'
        else:
            yield f'{outer + ":":10} {subtotal:>8}'
        if outer in bygroup:
            for inner, count in bygroup[outer].items():
                yield f'   {inner + ":":9} {count}'
    total = f'*{summary["totals"]["all"]}*'
    label = '*total*:'
    if bygroup:
        yield f'{label:20} {total:>8}'
    else:
        yield f'{label:10} {total:>9}'