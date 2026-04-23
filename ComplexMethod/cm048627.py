def _order_to_sql(self, order: str, query: Query, alias: (str | None) = None, reverse: bool = False) -> SQL:
        sql_order = super()._order_to_sql(order, query, alias, reverse)

        if order == self._order and (preferred_account_type := self.env.context.get('preferred_account_type')):
            sql_order = SQL(
                "%(field_sql)s = %(preferred_account_type)s %(direction)s, %(base_order)s",
                field_sql=self._field_to_sql(alias or self._table, 'account_type'),
                preferred_account_type=preferred_account_type,
                direction=SQL('ASC') if reverse else SQL('DESC'),
                base_order=sql_order,
            )
        if order == self._order and (preferred_account_ids := self.env.context.get('preferred_account_ids')):
            sql_order = SQL(
                "%(alias)s.id in %(preferred_account_ids)s %(direction)s, %(base_order)s",
                alias=SQL.identifier(alias or self._table),
                preferred_account_ids=tuple(map(int, preferred_account_ids)),
                direction=SQL('ASC') if reverse else SQL('DESC'),
                base_order=sql_order,
            )
        return sql_order