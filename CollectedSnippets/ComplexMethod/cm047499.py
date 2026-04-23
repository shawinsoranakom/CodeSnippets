def condition_to_sql(self, field_expr: str, operator: str, value, model: BaseModel, alias: str, query: Query) -> SQL:
        assert field_expr == self.name, "Supporting condition only to field"
        comodel = model.env[self.comodel_name]
        if not self.store:
            raise ValueError(f"Cannot convert {self} to SQL because it is not stored")

        # update the operator to 'any'
        if operator in ('in', 'not in'):
            operator = 'any' if operator == 'in' else 'not any'
        assert operator in ('any', 'not any', 'any!', 'not any!'), \
            f"Relational field {self} expects 'any' operator"
        exists = operator in ('any', 'any!')

        # check the value and execute the query
        if isinstance(value, COLLECTION_TYPES):
            value = OrderedSet(value)
            comodel = comodel.sudo().with_context(active_test=False)
            if False in value:
                #  [not]in (False, 1) => split conditions
                #  We want records that have a record such as condition or
                #  that don't have any records.
                if len(value) > 1:
                    in_operator = 'in' if exists else 'not in'
                    return SQL(
                        "(%s OR %s)" if exists else "(%s AND %s)",
                        self.condition_to_sql(field_expr, in_operator, (False,), model, alias, query),
                        self.condition_to_sql(field_expr, in_operator, value - {False}, model, alias, query),
                    )
                #  in (False) => not any (Domain.TRUE)
                #  not in (False) => any (Domain.TRUE)
                value = comodel._search(Domain.TRUE)
                exists = not exists
            else:
                value = comodel.browse(value)._as_query(ordered=False)
        elif isinstance(value, SQL):
            # wrap SQL into a simple query
            comodel = comodel.sudo()
            value = Domain('id', 'any', value)
        coquery = self._get_query_for_condition_value(model, comodel, operator, value)
        return self._condition_to_sql_relational(model, alias, exists, coquery, query)