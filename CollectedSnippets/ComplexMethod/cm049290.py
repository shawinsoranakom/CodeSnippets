def formatted_read_grouping_sets(
        self,
        domain: DomainType,
        grouping_sets: Sequence[Sequence[str]],
        aggregates: Sequence[str] = (),
        *,
        order: str | None = None,
    ):
        """
        A method similar to :meth:`_read_grouping_set` but with all the
        formatting needed by the webclient.
        It is a multi groupby version of formatted_read_group allowing to have
        aggregates for different groupby specifications in a single SQL requests.

        :param domain: :ref:`A search domain <reference/orm/domains>`.
            Use an empty list to match all records.
        :param grouping_sets: list of list of groupby descriptions by which the
            records will be grouped.

            A groupby description is either a field (then it will be
            grouped by that field) or a string
            ``'<field>:<granularity>'``.

            Right now, the only supported granularities are:

            * ``day``
            * ``week``
            * ``month``
            * ``quarter``
            * ``year``

            and they only make sense for date/datetime fields.

            Additionally integer date parts are also supported:

            * ``year_number``
            * ``quarter_number``
            * ``month_number``
            * ``iso_week_number``
            * ``day_of_year``
            * ``day_of_month``
            * ``day_of_week``
            * ``hour_number``
            * ``minute_number``
            * ``second_number``

        :param aggregates: list of aggregates specification. Each
            element is ``'<field>:<agg>'`` (aggregate field with
            aggregation function ``agg``). The possible aggregation
            functions are the ones provided by
            `PostgreSQL <https://www.postgresql.org/docs/current/static/functions-aggregate.html>`_,
            except ``count_distinct`` and ``array_agg_distinct`` with
            the expected meaning.

        :param order: optional ``order by`` specification, for
            overriding the natural sort ordering of the groups, see
            :meth:`~.search`.

        :return: list of list of dict such as
            ``[[{'groupy_spec': value, ...}, ...], ...]`` containing:

            * the groupby values: ``{groupby[i]: <value>}``
            * the aggregate values: ``{aggregates[i]: <value>}``
            * ``'__extra_domain'``: list of tuples specifying the group
              search criteria
            * ``'__fold'``: boolean if a fold_name is set on the comodel
              and read_group_expand is activated

        :raise AccessError: if user is not allowed to access requested
            information
        """
        grouping_sets = [tuple(groupby) for groupby in grouping_sets]
        aggregates = tuple(agg.replace(':recordset', ':array_agg') for agg in aggregates)

        if not order:
            order = ', '.join(unique(spec for groupby in grouping_sets for spec in groupby))

        groups_list = self._read_grouping_sets(
            domain, grouping_sets, aggregates, order=order,
        )

        for groups_index, groupby in enumerate(grouping_sets):
            if self._web_read_group_field_expand(groupby):
                groups_list[groups_index] = self._web_read_group_expand(domain, groups_list[groups_index], groupby[0], aggregates, order)

        for groups_index, groupby in enumerate(grouping_sets):
            fill_temporal = self.env.context.get('fill_temporal')
            if groupby and (fill_temporal or isinstance(fill_temporal, dict)):
                if not isinstance(fill_temporal, dict):
                    fill_temporal = {}
                # This assumes that existing data is sorted by field 'groupby_name'
                groups_list[groups_index] = self._web_read_group_fill_temporal(groups_list[groups_index], groupby, aggregates, **fill_temporal)

        return [
            self._web_read_group_format(groupby, aggregates, groups)
            for groupby, groups in zip(grouping_sets, groups_list)
        ]