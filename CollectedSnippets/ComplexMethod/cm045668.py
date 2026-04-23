def _table_join(
        left: Joinable,
        right: Joinable,
        *on: expr.ColumnExpression,
        mode: JoinMode,
        id: expr.ColumnReference | None = None,
        left_instance: expr.ColumnReference | None = None,
        right_instance: expr.ColumnReference | None = None,
        exact_match: bool = False,  # if True do not optionalize output columns even if other than inner join is used
        left_exactly_once: bool = False,
        right_exactly_once: bool = False,
    ) -> JoinResult:
        if left == right:
            raise ValueError(
                "Cannot join table with itself. Use <table>.copy() as one of the arguments of the join."
            )

        left_table, left_substitutions = left._substitutions()
        right_table, right_substitutions = right._substitutions()

        chained_join_desugaring = SubstitutionDesugaring(
            {**left_substitutions, **right_substitutions}
        )

        if id is not None:
            id = chained_join_desugaring.eval_expression(id)
            id_column = id._column
        else:
            id_column = None

        common_column_names: StableSet[str] = StableSet()
        if left_instance is not None and right_instance is not None:
            on = (*on, left_instance == right_instance)
            last_column_is_instance = True
        else:
            assert left_instance is None and right_instance is None
            last_column_is_instance = False

        on_ = tuple(validate_shape(cond) for cond in on)

        for cond in on_:
            cond_left = cast(expr.ColumnReference, cond._left)
            cond_right = cast(expr.ColumnReference, cond._right)
            if cond_left.name == cond_right.name:
                common_column_names.add(cond_left.name)

        on_ = tuple(chained_join_desugaring.eval_expression(cond) for cond in on_)

        for cond in on_:
            validate_join_condition(cond, left_table, right_table)

        on_left = tuple(
            left_table._eval(cond._left, left_table._table_restricted_context)
            for cond in on_
        )
        on_right = tuple(
            right_table._eval(cond._right, right_table._table_restricted_context)
            for cond in on_
        )

        swp = id_column is not None and id_column is right_table._id_column
        assert (
            id_column is None
            or (id_column is left_table._id_column)
            or (id_column is right_table._id_column)
        )

        left_context_table = clmn.ContextTable(universe=left._universe, columns=on_left)
        right_context_table = clmn.ContextTable(
            universe=right._universe, columns=on_right
        )
        substitution: dict[thisclass.ThisMetaclass, Joinable] = {
            thisclass.left: left,
            thisclass.right: right,
        }
        universe = JoinResult._compute_universe(
            left_table, right_table, id_column, mode
        )
        if swp:
            context = clmn.JoinContext(
                universe,
                right_table,
                left_table,
                right_context_table,
                left_context_table,
                last_column_is_instance=last_column_is_instance,
                assign_id=id_column is not None,
                left_ear=mode in [JoinMode.RIGHT, JoinMode.OUTER],
                right_ear=mode in [JoinMode.LEFT, JoinMode.OUTER],
                exact_match=exact_match,
                left_exactly_once=left_exactly_once,
                right_exactly_once=right_exactly_once,
            )
        else:
            context = clmn.JoinContext(
                universe,
                left_table,
                right_table,
                left_context_table,
                right_context_table,
                last_column_is_instance=last_column_is_instance,
                assign_id=id_column is not None,
                left_ear=mode in [JoinMode.LEFT, JoinMode.OUTER],
                right_ear=mode in [JoinMode.RIGHT, JoinMode.OUTER],
                exact_match=exact_match,
                left_exactly_once=left_exactly_once,
                right_exactly_once=right_exactly_once,
            )
        inner_table, columns_mapping = JoinResult._prepare_inner_table_with_mapping(
            context,
            left,
            right,
            common_column_names,
        )
        return JoinResult(
            context,
            inner_table,
            columns_mapping,
            left_table,
            right_table,
            left,
            right,
            substitution,
            common_column_names,
            mode,
        )