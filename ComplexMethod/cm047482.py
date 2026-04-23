def _condition_to_sql(self, field_expr: str, operator: str, value, model: BaseModel, alias: str, query: Query) -> SQL:
        sql_field = model._field_to_sql(alias, field_expr, query)

        if field_expr == self.name:
            def _value_to_column(v):
                return self.convert_to_column(v, model, validate=False)
        else:
            # reading a property, keep value as-is
            def _value_to_column(v):
                return v

        # support for SQL value
        if operator in SQL_OPERATORS and isinstance(value, SQL):
            warnings.warn("Since 19.0, use Domain.custom(to_sql=lambda model, alias, query: SQL(...))", DeprecationWarning)
            return SQL("%s%s%s", sql_field, SQL_OPERATORS[operator], value)

        # nullability
        can_be_null = self not in model.env.registry.not_null_fields

        # operator: in (equality)
        if operator in ('in', 'not in'):
            assert isinstance(value, COLLECTION_TYPES), \
                f"condition_to_sql() 'in' operator expects a collection, not a {value!r}"
            params = tuple(_value_to_column(v) for v in value if v is not False and v is not None)
            null_in_condition = len(params) < len(value)
            # if we have a value treated as null
            if (null_value := self.falsy_value) is not None:
                null_value = _value_to_column(null_value)
                if null_value in params:
                    null_in_condition = True
                elif null_in_condition:
                    params = (*params, null_value)

            sql = None
            if params:
                sql = SQL("%s%s%s", sql_field, SQL_OPERATORS[operator], params)

            if (operator == 'in') == null_in_condition:
                # field in {val, False} => field IN vals OR field IS NULL
                # field not in {val} => field NOT IN vals OR field IS NULL
                if not can_be_null:
                    return sql or SQL("FALSE")
                sql_null = SQL("%s IS NULL", sql_field)
                return SQL("(%s OR %s)", sql, sql_null) if sql else sql_null

            elif operator == 'not in' and null_in_condition and not sql:
                # if we have a base query, null values are already exluded
                return SQL("%s IS NOT NULL", sql_field) if can_be_null else SQL("TRUE")

            assert sql, f"Missing sql query for {operator} {value!r}"
            return sql

        # operator: like
        if operator.endswith('like'):
            # cast value to text for any like comparison
            sql_left = sql_field if self.is_text else SQL("%s::text", sql_field)

            # add wildcard and unaccent depending on the operator
            need_wildcard = '=' not in operator
            if need_wildcard:
                sql_value = SQL("%s", f"%{value}%")
            else:
                sql_value = SQL("%s", str(value))
            if operator.endswith('ilike'):
                sql_left = model.env.registry.unaccent(sql_left)
                sql_value = model.env.registry.unaccent(sql_value)

            sql = SQL("%s%s%s", sql_left, SQL_OPERATORS[operator], sql_value)
            if operator in Domain.NEGATIVE_OPERATORS and can_be_null:
                sql = SQL("(%s OR %s IS NULL)", sql, sql_field)
            return sql

        # operator: inequality
        if operator in ('>', '<', '>=', '<='):
            accept_null_value = False
            if (null_value := self.falsy_value) is not None:
                value = self.convert_to_cache(value, model) or null_value
                accept_null_value = can_be_null and (
                    null_value < value if operator == '<' else
                    null_value > value if operator == '>' else
                    null_value <= value if operator == '<=' else
                    null_value >= value  # operator == '>='
                )
            sql_value = SQL("%s", _value_to_column(value))

            sql = SQL("%s%s%s", sql_field, SQL_OPERATORS[operator], sql_value)
            if accept_null_value:
                sql = SQL("(%s OR %s IS NULL)", sql, sql_field)
            return sql

        # operator: any
        # Note: relational operators overwrite this function for a more specific
        # behaviour, here we check just the field against the subselect.
        # Example usage: ('id', 'any!', Query | SQL)
        if operator in ('any!', 'not any!'):
            if isinstance(value, Query):
                subselect = value.subselect()
            elif isinstance(value, SQL):
                subselect = SQL("(%s)", value)
            else:
                raise TypeError(f"condition_to_sql() operator 'any!' accepts SQL or Query, got {value}")
            sql_operator = SQL_OPERATORS["in" if operator == "any!" else "not in"]
            return SQL("%s%s%s", sql_field, sql_operator, subselect)

        raise NotImplementedError(f"Invalid operator {operator!r} for SQL in domain term {(field_expr, operator, value)!r}")