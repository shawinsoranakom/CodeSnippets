def get_fallback_sql(self, compiler, connection):
        rhs = self.rhs
        if not rhs:
            raise EmptyResultSet
        if isinstance(rhs, Query):
            rhs_exprs = itertools.chain.from_iterable(
                (
                    select_expr
                    if isinstance((select_expr := select[0]), ColPairs)
                    else [select_expr]
                )
                for select in rhs.get_compiler(connection=connection).get_select()[0]
            )
            rhs = rhs.clone()
            rhs.add_q(
                models.Q(*[Exact(col, val) for col, val in zip(self.lhs, rhs_exprs)])
            )
            return compiler.compile(Exists(rhs))
        elif not self.rhs_is_direct_value():
            return super(TupleLookupMixin, self).as_sql(compiler, connection)

        # e.g.: (a, b, c) in [(x1, y1, z1), (x2, y2, z2)] as SQL:
        # WHERE (a = x1 AND b = y1 AND c = z1)
        #    OR (a = x2 AND b = y2 AND c = z2)
        root = WhereNode([], connector=OR)
        lhs = self.lhs

        for vals in rhs:
            # Remove any tuple containing None from the list as NULL is never
            # equal to anything.
            if any(val is None for val in vals):
                continue
            lookups = [Exact(col, val) for col, val in zip(lhs, vals)]
            root.children.append(WhereNode(lookups, connector=AND))

        if not root.children:
            raise EmptyResultSet
        return root.as_sql(compiler, connection)