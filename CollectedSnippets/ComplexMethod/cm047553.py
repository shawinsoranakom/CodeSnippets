def _read_group(
        self,
        domain: DomainType,
        groupby: Sequence[str] = (),
        aggregates: Sequence[str] = (),
        having: DomainType = (),
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[tuple]:
        """ Get fields aggregations specified by ``aggregates`` grouped by the given ``groupby``
        fields where record are filtered by the ``domain``.

        :param domain: :ref:`A search domain <reference/orm/domains>`. Use an empty
                list to match all records.
        :param groupby: list of groupby descriptions by which the records will be grouped.
                A groupby description is either a field (then it will be grouped by that field)
                or a string `'field:granularity'`. Right now, the only supported granularities
                are `'day'`, `'week'`, `'month'`, `'quarter'` or `'year'`, and they only make sense for
                date/datetime fields.
                Additionally integer date parts are also supported:
                `'year_number'`, `'quarter_number'`, `'month_number'`, `'iso_week_number'`, `'day_of_year'`, `'day_of_month'`,
                'day_of_week', 'hour_number', 'minute_number' and 'second_number'.
        :param aggregates: list of aggregates specification.
                Each element is `'field:agg'` (aggregate field with aggregation function `'agg'`).
                The possible aggregation functions are the ones provided by
                `PostgreSQL <https://www.postgresql.org/docs/current/static/functions-aggregate.html>`_,
                `'count_distinct'` with the expected meaning and `'recordset'` to act like `'array_agg'`
                converted into a recordset.
        :param having: A domain where the valid "fields" are the aggregates.
        :param offset: optional number of groups to skip
        :param limit: optional max number of groups to return
        :param order: optional ``order by`` specification, for
                overriding the natural sort ordering of the groups,
                see also :meth:`~.search`.
        :return: list of tuples containing in the order the groups values and aggregates values (flatten):
                `[(groupby_1_value, ... , aggregate_1_value_aggregate, ...), ...]`.
                If group is related field, the value of it will be a recordset (with a correct prefetch set).

        :raise AccessError: if user is not allowed to access requested information
        """
        self.browse().check_access('read')

        query = self._search(domain)
        if query.is_empty():
            if not groupby:
                # when there is no group, postgresql always return a row
                return [tuple(
                    self._read_group_empty_value(spec)
                    for spec in itertools.chain(groupby, aggregates)
                )]
            return []

        query.limit = limit
        query.offset = offset

        groupby_terms: dict[str, SQL] = {
            spec: self._read_group_groupby(self._table, spec, query)
            for spec in groupby
        }
        aggregates_terms: list[SQL] = [
            self._read_group_select(spec, query)
            for spec in aggregates
        ]
        select_args = [*[groupby_terms[spec] for spec in groupby], *aggregates_terms]
        if groupby_terms:
            query.order = self._read_group_orderby(order, groupby_terms, query)
            query.groupby = SQL(", ").join(groupby_terms.values())
            query.having = self._read_group_having(list(having), query)

        # row_values: [(a1, b1, c1), (a2, b2, c2), ...]
        row_values = self.env.execute_query(query.select(*select_args))

        if not row_values:
            return row_values

        # post-process values column by column
        column_iterator = zip(*row_values)

        # column_result: [(a1, a2, ...), (b1, b2, ...), (c1, c2, ...)]
        column_result = []
        for spec in groupby:
            column = self._read_group_postprocess_groupby(spec, next(column_iterator))
            column_result.append(column)
        for spec in aggregates:
            column = self._read_group_postprocess_aggregate(spec, next(column_iterator))
            column_result.append(column)
        assert next(column_iterator, None) is None

        # return [(a1, b1, c1), (a2, b2, c2), ...]
        return list(zip(*column_result))