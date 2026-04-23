def _asof_now_join(
        left: pw.Table,
        right: pw.Table,
        *on: expr.ColumnExpression,
        mode: pw.JoinMode,
        id: expr.ColumnReference | None = None,
        left_instance: expr.ColumnReference | None = None,
        right_instance: expr.ColumnReference | None = None,
        exact_match: bool = False,  # if True do not optionalize output columns even if other than inner join is used
    ) -> AsofNowJoinResult:
        # TODO assert that left is append-only

        if mode != pw.JoinMode.INNER and mode != pw.JoinMode.LEFT:
            raise ValueError(
                "asof_now_join can only use modes pathway.JoinMode.INNER or pathway.JoinMode.LEFT"
            )

        left_with_forgetting = left._forget_immediately()
        if left_instance is not None and right_instance is not None:
            on = (*on, left_instance == right_instance)
        else:
            assert left_instance is None and right_instance is None
        for cond in on:
            cond_left, _, cond = validate_join_condition(cond, left, right)
            cond._left = left_with_forgetting[cond_left._name]
        if id is not None and id.table == left:
            id = left_with_forgetting[id._name]

        table_substitution: dict[pw.TableLike, pw.Table] = {
            left: left_with_forgetting,
        }
        join_result = JoinResult._table_join(
            left_with_forgetting, right, *on, id=id, mode=mode, exact_match=exact_match
        )

        return AsofNowJoinResult(
            original_left=left,
            left=left_with_forgetting,
            right=right,
            join_result=join_result,
            table_substitution=table_substitution,
            mode=mode,
            id=id,
        )