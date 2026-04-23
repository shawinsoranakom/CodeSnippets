def _read_group_orderby(self, order: str, groupby_terms: dict[str, SQL],
                            query: Query) -> SQL:
        """ Return (<SQL expression>, <SQL expression>)
        corresponding to the given order and groupby terms.

        Note: this method may change groupby_terms

        :param order: the order specification
        :param groupby_terms: the group by terms mapping ({spec: sql_expression})
        :param query: The query we are building
        """
        if order:
            traverse_many2one = True
        else:
            order = ','.join(groupby_terms)
            traverse_many2one = False

        if not order:
            return SQL()

        orderby_terms = []

        for order_part in order.split(','):
            order_match = regex_order_part_read_group.fullmatch(order_part)
            if not order_match:
                raise ValueError(f"Invalid order {order!r} for _read_group()")
            term = order_match['term']
            direction = (order_match['direction'] or 'ASC').upper()
            nulls = (order_match['nulls'] or '').upper()

            sql_direction = SQL(direction) if direction in ('ASC', 'DESC') else SQL()
            sql_nulls = SQL(nulls) if nulls in ('NULLS FIRST', 'NULLS LAST') else SQL()

            if term not in groupby_terms:
                try:
                    sql_expr = self._read_group_select(term, query)
                except ValueError as e:
                    raise ValueError(f"Order term {order_part!r} is not a valid aggregate nor valid groupby") from e
                orderby_terms.append(SQL("%s %s %s", sql_expr, sql_direction, sql_nulls))
                continue

            field = self._fields.get(term)
            __, __, granularity = parse_read_group_spec(term)
            if (
                traverse_many2one and field and field.type == 'many2one'
                and self.env[field.comodel_name]._order != 'id'
            ):
                if sql_order := self._order_to_sql(f'{term} {direction} {nulls}', query):
                    orderby_terms.append(sql_order)
                    if query._order_groupby:
                        groupby_terms[term] = SQL(", ").join([groupby_terms[term], *query._order_groupby])
                        query._order_groupby.clear()

            elif granularity == 'day_of_week':
                """
                Day offset relative to the first day of week in the user lang
                formula: ((7 - first_week_day) + day_in_SQL) % 7

                               | week starts on
                           SQL | mon   sun   sat
                               |  1  |  7  |  6   <-- first_week_day (in odoo)
                          -----|-----------------
                    mon     1  |  0  |  1  |  2
                    tue     2  |  1  |  2  |  3
                    wed     3  |  2  |  3  |  4
                    thu     4  |  3  |  4  |  5
                    fri     5  |  4  |  5  |  6
                    sat     6  |  5  |  6  |  0
                    sun     0  |  6  |  0  |  1
                """
                first_week_day = int(get_lang(self.env).week_start)
                sql_expr = SQL("mod(7 - %s + %s::int, 7)", first_week_day, groupby_terms[term])
                orderby_terms.append(SQL("%s %s %s", sql_expr, sql_direction, sql_nulls))
            else:
                sql_expr = groupby_terms[term]
                orderby_terms.append(SQL("%s %s %s", sql_expr, sql_direction, sql_nulls))

        return SQL(", ").join(orderby_terms)