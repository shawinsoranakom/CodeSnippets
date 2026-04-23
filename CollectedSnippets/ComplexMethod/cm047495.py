def condition_to_sql(self, field_expr: str, operator: str, value, model: BaseModel, alias: str, query: Query) -> SQL:
        if operator not in ('any', 'not any', 'any!', 'not any!') or field_expr != self.name:
            # for other operators than 'any', just generate condition based on column type
            return super().condition_to_sql(field_expr, operator, value, model, alias, query)

        comodel = model.env[self.comodel_name]
        sql_field = model._field_to_sql(alias, field_expr, query)
        can_be_null = self not in model.env.registry.not_null_fields
        bypass_access = operator in ('any!', 'not any!') or self.bypass_search_access
        positive = operator in ('any', 'any!')

        # Decide whether to use a LEFT JOIN
        left_join = bypass_access and isinstance(value, Domain)
        if left_join and not positive:
            # For 'not any!', we get a better query with a NOT IN when we have a
            # lot of positive conditions which have a better chance to use
            # indexes.
            #   `field NOT IN (SELECT ... WHERE z = y)` better than
            #   `LEFT JOIN ... ON field = id WHERE z <> y`
            # There are some exceptions: we filter on 'id'.
            left_join = sum(
                (-1 if cond.operator in Domain.NEGATIVE_OPERATORS else 1)
                for cond in value.iter_conditions()
            ) < 0 or any(
                cond.field_expr == 'id' and cond.operator not in Domain.NEGATIVE_OPERATORS
                for cond in value.iter_conditions()
            )

        if left_join:
            comodel, coalias = self.join(model, alias, query)
            if not positive:
                value = (~value).optimize_full(comodel)
            sql = value._to_sql(comodel, coalias, query)
            if self.company_dependent:
                sql = self._condition_to_sql_company(sql, field_expr, operator, value, model, alias, query)
            if can_be_null:
                if positive:
                    sql = SQL("(%s IS NOT NULL AND %s)", sql_field, sql)
                else:
                    sql = SQL("(%s IS NULL OR %s)", sql_field, sql)
            return sql

        if isinstance(value, Domain):
            value = comodel._search(value, active_test=False, bypass_access=bypass_access)
        if isinstance(value, Query):
            subselect = value.subselect()
        elif isinstance(value, SQL):
            subselect = SQL("(%s)", value)
        else:
            raise TypeError(f"condition_to_sql() 'any' operator accepts Domain, SQL or Query, got {value}")
        sql = SQL(
            "%s%s%s",
            sql_field,
            SQL(" IN ") if positive else SQL(" NOT IN "),
            subselect,
        )
        if can_be_null and not positive:
            sql = SQL("(%s IS NULL OR %s)", sql_field, sql)
        if self.company_dependent:
            sql = self._condition_to_sql_company(sql, field_expr, operator, value, model, alias, query)
        return sql