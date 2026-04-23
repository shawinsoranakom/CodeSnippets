def _order_to_sql(self, order: str, query: Query, alias: (str | None) = None,
                      reverse: bool = False) -> SQL:
        """ Return an :class:`SQL` object that represents the given ORDER BY
        clause, without the ORDER BY keyword.  The method also checks whether
        the fields in the order are accessible for reading.
        """
        order = order or self._order
        if not order:
            return SQL()
        self._check_qorder(order)

        alias = alias or self._table

        terms = []
        for order_part in order.split(','):
            order_match = regex_order.match(order_part)
            assert order_match is not None, "No match found"
            field_name = order_match['field']

            direction = (order_match['direction'] or '').upper()
            nulls = (order_match['nulls'] or '').upper()
            if reverse:
                direction = 'ASC' if direction == 'DESC' else 'DESC'
                if nulls:
                    nulls = 'NULLS LAST' if nulls == 'NULLS FIRST' else 'NULLS FIRST'

            sql_direction = SQL(direction) if direction in ('ASC', 'DESC') else SQL()
            sql_nulls = SQL(nulls) if nulls in ('NULLS FIRST', 'NULLS LAST') else SQL()

            if property_name := order_match['property']:
                # field_name is an expression
                field_name = f"{field_name}.{property_name}"
            term = self._order_field_to_sql(alias, field_name, sql_direction, sql_nulls, query)
            if term:
                terms.append(term)

        return SQL(", ").join(terms)