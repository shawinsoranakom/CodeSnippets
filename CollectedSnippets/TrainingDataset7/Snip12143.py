def get_qualify_sql(self):
        where_parts = []
        if self.where:
            where_parts.append(self.where)
        if self.having:
            where_parts.append(self.having)
        inner_query = self.query.clone()
        inner_query.subquery = True
        inner_query.where = inner_query.where.__class__(where_parts)
        # Augment the inner query with any window function references that
        # might have been masked via values() and alias(). If any masked
        # aliases are added they'll be masked again to avoid fetching
        # the data in the `if qual_aliases` branch below.
        select = {
            expr: alias for expr, _, alias in self.get_select(with_col_aliases=True)[0]
        }
        select_aliases = set(select.values())
        qual_aliases = set()
        replacements = {}

        def collect_replacements(expressions):
            while expressions:
                expr = expressions.pop()
                if expr in replacements:
                    continue
                elif select_alias := select.get(expr):
                    replacements[expr] = select_alias
                elif isinstance(expr, Lookup):
                    expressions.extend(expr.get_source_expressions())
                elif isinstance(expr, Ref):
                    if expr.refs not in select_aliases:
                        expressions.extend(expr.get_source_expressions())
                else:
                    num_qual_alias = len(qual_aliases)
                    select_alias = f"qual{num_qual_alias}"
                    qual_aliases.add(select_alias)
                    inner_query.add_annotation(expr, select_alias)
                    replacements[expr] = select_alias

        collect_replacements(list(self.qualify.leaves()))
        self.qualify = self.qualify.replace_expressions(
            {expr: Ref(alias, expr) for expr, alias in replacements.items()}
        )
        order_by = []
        for order_by_expr, *_ in self.get_order_by():
            collect_replacements(order_by_expr.get_source_expressions())
            order_by.append(
                order_by_expr.replace_expressions(
                    {expr: Ref(alias, expr) for expr, alias in replacements.items()}
                )
            )
        inner_query_compiler = inner_query.get_compiler(
            self.using, connection=self.connection, elide_empty=self.elide_empty
        )
        inner_sql, inner_params = inner_query_compiler.as_sql(
            # The limits must be applied to the outer query to avoid pruning
            # results too eagerly.
            with_limits=False,
            # Force unique aliasing of selected columns to avoid collisions
            # and make rhs predicates referencing easier.
            with_col_aliases=True,
        )
        qualify_sql, qualify_params = self.compile(self.qualify)
        result = [
            "SELECT * FROM (",
            inner_sql,
            ")",
            self.connection.ops.quote_name("qualify"),
            "WHERE",
            qualify_sql,
        ]
        if qual_aliases:
            # If some select aliases were unmasked for filtering purposes they
            # must be masked back.
            cols = [self.connection.ops.quote_name(alias) for alias in select.values()]
            result = [
                "SELECT",
                ", ".join(cols),
                "FROM (",
                *result,
                ")",
                self.connection.ops.quote_name("qualify_mask"),
            ]
        params = list(inner_params) + qualify_params
        # As the SQL spec is unclear on whether or not derived tables
        # ordering must propagate it has to be explicitly repeated on the
        # outer-most query to ensure it's preserved.
        if order_by:
            ordering_sqls = []
            for ordering in order_by:
                ordering_sql, ordering_params = self.compile(ordering)
                ordering_sqls.append(ordering_sql)
                params.extend(ordering_params)
            result.extend(["ORDER BY", ", ".join(ordering_sqls)])
        return result, params