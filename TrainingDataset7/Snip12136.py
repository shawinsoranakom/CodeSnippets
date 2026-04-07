def get_order_by(self):
        """
        Return a list of 2-tuples of the form (expr, (sql, params, is_ref)) for
        the ORDER BY clause.

        The order_by clause can alter the select clause (for example it can add
        aliases to clauses that do not yet have one, or it can add totally new
        select clauses).
        """
        result = []
        seen = set()
        for expr, is_ref in self._order_by_pairs():
            resolved = expr.resolve_expression(self.query, allow_joins=True, reuse=None)
            if not is_ref and self.query.combinator and self.select:
                src = resolved.expression
                expr_src = expr.expression
                for sel_expr, _, col_alias in self.select:
                    if src == sel_expr:
                        # When values() is used the exact alias must be used to
                        # reference annotations.
                        if (
                            self.query.has_select_fields
                            and col_alias in self.query.annotation_select
                            and not (
                                isinstance(expr_src, F) and col_alias == expr_src.name
                            )
                        ):
                            continue
                        resolved.set_source_expressions(
                            [Ref(col_alias if col_alias else src.target.column, src)]
                        )
                        break
                else:
                    # Add column used in ORDER BY clause to the selected
                    # columns and to each combined query.
                    order_by_idx = len(self.query.select) + 1
                    col_alias = f"__orderbycol{order_by_idx}"
                    for q in self.query.combined_queries:
                        # If fields were explicitly selected through values()
                        # combined queries cannot be augmented.
                        if q.has_select_fields:
                            raise DatabaseError(
                                "ORDER BY term does not match any column in "
                                "the result set."
                            )
                        q.add_annotation(expr_src, col_alias)
                    self.query.add_select_col(resolved, col_alias)
                    resolved.set_source_expressions([Ref(col_alias, src)])
            sql, params = self.compile(resolved)
            # Don't add the same column twice, but the order direction is
            # not taken into account so we strip it. When this entire method
            # is refactored into expressions, then we can check each part as we
            # generate it.
            without_ordering = self.ordering_parts.search(sql)[1]
            params_hash = make_hashable(params)
            if (without_ordering, params_hash) in seen:
                continue
            seen.add((without_ordering, params_hash))
            result.append((resolved, (sql, params, is_ref)))
        return result