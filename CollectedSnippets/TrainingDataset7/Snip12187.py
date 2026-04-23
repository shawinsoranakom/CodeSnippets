def as_sql(self, compiler, connection):
        """
        Generate the full
           LEFT OUTER JOIN sometable
           ON sometable.somecol = othertable.othercol, params
        clause for this join.
        """
        join_conditions = []
        params = []
        qn = compiler.quote_name
        # Add a join condition for each pair of joining columns.
        for lhs, rhs in self.join_fields:
            lhs, rhs = connection.ops.prepare_join_on_clause(
                self.parent_alias, lhs, self.table_alias, rhs
            )
            lhs_sql, lhs_params = compiler.compile(lhs)
            lhs_full_name = lhs_sql % lhs_params
            rhs_sql, rhs_params = compiler.compile(rhs)
            rhs_full_name = rhs_sql % rhs_params
            join_conditions.append(f"{lhs_full_name} = {rhs_full_name}")

        # Add a single condition inside parentheses for whatever
        # get_extra_restriction() returns.
        extra_cond = self.join_field.get_extra_restriction(
            self.table_alias, self.parent_alias
        )
        if extra_cond:
            extra_sql, extra_params = compiler.compile(extra_cond)
            join_conditions.append("(%s)" % extra_sql)
            params.extend(extra_params)
        if self.filtered_relation:
            try:
                extra_sql, extra_params = compiler.compile(self.filtered_relation)
            except FullResultSet:
                pass
            else:
                join_conditions.append("(%s)" % extra_sql)
                params.extend(extra_params)
        if not join_conditions:
            # This might be a rel on the other end of an actual declared field.
            declared_field = getattr(self.join_field, "field", self.join_field)
            raise ValueError(
                "Join generated an empty ON clause. %s did not yield either "
                "joining columns or extra restrictions." % declared_field.__class__
            )
        on_clause_sql = " AND ".join(join_conditions)
        alias_str = (
            ""
            if self.table_alias == self.table_name
            else (" %s" % qn(self.table_alias))
        )
        sql = "%s %s%s ON (%s)" % (
            self.join_type,
            qn(self.table_name),
            alias_str,
            on_clause_sql,
        )
        return sql, params