def _select(
    node: sql_expr.Select, context: ContextType
) -> tuple[table.Table, ContextType]:
    orig_context = context

    # WITH block
    context = _with_block(node, context)

    # FROM block
    tab, context = _from(node.args.pop("from"), context)

    tab, context = _joins_block(node, tab, context)

    # GROUP block
    if (group_field := node.args.pop("group", None)) is not None:
        groupby = _group(group_field, context)
    else:
        groupby = None

    # args building
    expr_args = []
    expr_kwargs = {}
    for e in node.args.pop("expressions"):
        ret = _run(e, context)
        if isinstance(ret, dict):
            expr_kwargs.update(ret)
        else:
            expr_args.append(ret)

    # WHERE block
    if (where_field := node.args.pop("where", None)) is not None:
        # mutates `where_field`
        tab_joined_where, context_subqueries_where = _process_field_for_subqueries(
            where_field, tab, context, orig_context, ""
        )

        tab_filter_where = tab_joined_where.select(
            filter_col=_where(where_field, context_subqueries_where)
        ).with_universe_of(tab)
        tab_filtered = tab.filter(tab_filter_where.filter_col)
        table_replacer = TableSubstitutionDesugaring({tab: tab_filtered})
        expr_args = [table_replacer.eval_expression(e) for e in expr_args]
        if groupby is not None:
            groupby = [table_replacer.eval_expression(e) for e in groupby]
        expr_kwargs = {
            name: table_replacer.eval_expression(e) for name, e in expr_kwargs.items()
        }
        tab = tab_filtered

    # HAVING block
    if (having_field := node.args.pop("having", None)) is not None:
        if groupby is None:
            groupby = []

    _check_work_done(node)

    # maybe we have implicit GROUP BY
    if groupby is None:
        detector = ReducerDetector()
        for arg in expr_args:
            detector.eval_expression(arg)
        for arg in expr_kwargs.values():
            detector.eval_expression(arg)
        if detector.contains_reducers:
            groupby = []

    if groupby is None:
        result = tab.select(*expr_args, **expr_kwargs)
        return result, orig_context

    if having_field is not None:
        # mutates `having_field`
        tab, context_subqueries_having = _process_field_for_subqueries(
            having_field, tab, context, orig_context, "MIN"
        )
        having_expr = _having(having_field, context_subqueries_having)
        gatherer = _ReducersGatherer()
        having_expr = gatherer.eval_expression(having_expr)
        expr_kwargs = {**expr_kwargs, **gatherer.gathered_reducers}

    grouped = tab.groupby(*groupby)
    result = grouped.reduce(*expr_args, **expr_kwargs)
    if having_field is None:
        return result, orig_context

    having_col = _HavingHelper(result).eval_expression(having_expr)
    result = result.filter(having_col).without(
        *[thisclass.this[name] for name in gatherer.gathered_reducers.keys()]
    )
    return result, orig_context