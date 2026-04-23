def _read_group_select(self, aggregate_spec: str, query: Query) -> SQL:
        """ Return <SQL expression> corresponding to the given aggregation.
        The method also checks whether the fields used in the aggregate are
        accessible for reading.
        """
        if aggregate_spec == '__count':
            return SQL("COUNT(*)")

        fname, property_name, func = parse_read_group_spec(aggregate_spec)

        if property_name:
            raise ValueError(f"Invalid {aggregate_spec!r}, this dot notation is not supported")

        if fname not in self._fields:
            raise ValueError(f"Invalid field {fname!r} on model {self._name!r} for {aggregate_spec!r}.")
        if not func:
            raise ValueError(f"Aggregate method is mandatory for {fname!r}")

        field = self._fields[fname]
        if func == 'sum_currency':
            if field.type != 'monetary':
                raise ValueError(f'Aggregator "sum_currency" only works on currency field for {fname!r}')

            CurrencyRate = self.env['res.currency.rate']
            rate_subquery_table = SQL(
                """(SELECT DISTINCT ON (%(currency_field_sql)s) %(currency_field_sql)s, %(rate_field_sql)s
                    FROM "res_currency_rate"
                    WHERE %(company_field_sql)s IS NULL OR %(company_field_sql)s = %(company_id)s
                    ORDER BY
                        %(currency_field_sql)s,
                        %(company_field_sql)s,
                        CASE WHEN %(name_field_sql)s <= %(today)s THEN %(name_field_sql)s END DESC,
                        CASE WHEN %(name_field_sql)s > %(today)s THEN %(name_field_sql)s END ASC)
                """,
                currency_field_sql=CurrencyRate._field_to_sql(CurrencyRate._table, 'currency_id'),
                rate_field_sql=CurrencyRate._field_to_sql(CurrencyRate._table, 'rate'),
                company_field_sql=CurrencyRate._field_to_sql(CurrencyRate._table, 'company_id'),
                company_id=self.env.company.root_id.id,
                name_field_sql=CurrencyRate._field_to_sql(CurrencyRate._table, 'name'),
                today=Date.context_today(self),
            )
            currency_field_name = field.get_currency_field(self)
            alias_rate = query.make_alias(self._table, f'{currency_field_name}__rates')
            currency_field_sql = self._field_to_sql(self._table, currency_field_name, query)
            condition = SQL("%s = %s", currency_field_sql, SQL.identifier(alias_rate, "currency_id"))
            query.add_join('LEFT JOIN', alias_rate, rate_subquery_table, condition)

            return SQL(
                "SUM(%s / COALESCE(%s, 1.0))",
                self._field_to_sql(self._table, fname, query),
                SQL.identifier(alias_rate, "rate"),
            )

        if func not in READ_GROUP_AGGREGATE:
            raise ValueError(f"Invalid aggregate method {func!r} for {aggregate_spec!r}.")

        if func == 'recordset' and not (field.relational or fname == 'id'):
            raise ValueError(f"Aggregate method {func!r} can be only used on relational field (or id) (for {aggregate_spec!r}).")

        sql_field = self._field_to_sql(self._table, fname, query)
        return READ_GROUP_AGGREGATE[func](self._table, sql_field)