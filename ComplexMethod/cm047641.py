def condition_to_sql(self, field_expr: str, operator: str, value, model: BaseModel, alias: str, query: Query) -> SQL:
        fname, property_name = parse_field_expr(field_expr)
        if not property_name:
            raise ValueError(f"Missing property name for {self}")
        raw_sql_field = model._field_to_sql(alias, fname, query)
        sql_left = model._field_to_sql(alias, field_expr, query)

        if operator in ('in', 'not in'):
            assert isinstance(value, COLLECTION_TYPES)
            if len(value) == 1 and True in value:
                # inverse the condition
                check_null_op_false = "!=" if operator == 'in' else "="
                value = []
                operator = 'in' if operator == 'not in' else 'not in'
            elif False in value:
                check_null_op_false = "=" if operator == 'in' else "!="
                value = [v for v in value if v]
            else:
                value = list(value)
                check_null_op_false = None

            sqls = []
            if check_null_op_false:
                sqls.append(SQL(
                    "%s%s'%s'",
                    sql_left,
                    SQL_OPERATORS[check_null_op_false],
                    False,
                ))
                if check_null_op_false == '=':
                    # check null value too
                    sqls.extend((
                        SQL("%s IS NULL", raw_sql_field),
                        SQL("NOT (%s ? %s)", raw_sql_field, property_name),
                    ))
            # left can be an array or a single value!
            # Even if we use the '=' operator, we must check the list subset.
            # There is an unsupported edge-case where left is a list and we
            # have multiple values.
            if len(value) == 1:
                # check single value equality
                sql_operator = SQL_OPERATORS['=' if operator == 'in' else '!=']
                sql_right = SQL("%s", json.dumps(value[0]))
                sqls.append(SQL("%s%s%s", sql_left, sql_operator, sql_right))
            if value:
                sql_not = SQL('NOT ') if operator == 'not in' else SQL()
                # hackish operator to search values
                if len(value) > 1:
                    # left <@ value_list -- single left value in value_list
                    # (here we suppose left is a single value)
                    sql_operator = SQL(" <@ ")
                else:
                    # left @> value -- value_list in left
                    sql_operator = SQL(" @> ")
                sql_right = SQL("%s", json.dumps(value))
                sqls.append(SQL(
                    "%s%s%s%s",
                    sql_not, sql_left, sql_operator, sql_right,
                ))
            assert sqls, "No SQL generated for property"
            if len(sqls) == 1:
                return sqls[0]
            combine_sql = SQL(" OR ") if operator == 'in' else SQL(" AND ")
            return SQL("(%s)", combine_sql.join(sqls))

        unaccent = lambda x: x  # noqa: E731
        if operator.endswith('like'):
            if operator.endswith('ilike'):
                unaccent = model.env.registry.unaccent
            if '=' in operator:
                value = str(value)
            else:
                value = f'%{value}%'

        try:
            sql_operator = SQL_OPERATORS[operator]
        except KeyError:
            raise ValueError(f"Invalid operator {operator} for Properties")

        if isinstance(value, str):
            sql_left = SQL("(%s ->> %s)", raw_sql_field, property_name)  # JSONified value
            sql_right = SQL("%s", value)
            sql = SQL(
                "%s%s%s",
                unaccent(sql_left), sql_operator, unaccent(sql_right),
            )
            if operator in Domain.NEGATIVE_OPERATORS:
                sql = SQL("(%s OR %s IS NULL)", sql, sql_left)
            return sql

        sql_right = SQL("%s", json.dumps(value))
        return SQL(
            "%s%s%s",
            unaccent(sql_left), sql_operator, unaccent(sql_right),
        )