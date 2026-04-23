def _prepare_inner_table_with_mapping(
        context: clmn.JoinContext,
        original_left: Joinable,
        original_right: Joinable,
        common_column_names: StableSet[str],
    ) -> tuple[Table, dict[expr.InternalColRef, expr.ColumnReference]]:
        left_table, left_substitutions = original_left._substitutions()
        right_table, right_substitutions = original_right._substitutions()
        cnt = itertools.count(0)
        expressions: dict[str, expr.ColumnExpression] = {}
        colref_to_name_mapping: dict[expr.InternalColRef, str] = {}
        for table, subs in [
            (left_table, left_substitutions),
            (right_table, right_substitutions),
        ]:
            if len(subs) == 0:  # tables have empty subs, so set them here
                for ref in table:
                    subs[ref._to_internal()] = ref
            subs_total = subs | {table.id._to_internal(): table.id}
            for int_ref, expression in subs_total.items():
                inner_name = f"_pw_{next(cnt)}"
                expressions[inner_name] = expression
                colref_to_name_mapping[int_ref] = inner_name
        from pathway.internals.common import coalesce

        for name in common_column_names:
            if name != "id":
                expressions[name] = coalesce(original_left[name], original_right[name])

        inner_table = JoinResult._join(context, **expressions)
        final_mapping = {
            colref: inner_table[name] for colref, name in colref_to_name_mapping.items()
        }
        for name in common_column_names:
            if name != "id":
                colref = inner_table[name]
                final_mapping[colref._to_internal()] = colref
        final_mapping[inner_table.id._to_internal()] = inner_table.id

        rowwise_context = clmn.JoinRowwiseContext.from_mapping(
            inner_table._id_column, final_mapping
        )
        inner_table._rowwise_context = (
            rowwise_context  # FIXME don't set _context property of table
        )

        return (inner_table, final_mapping)