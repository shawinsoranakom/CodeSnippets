def formatted_read_group(
        self,
        domain: DomainType,
        groupby: Sequence[str] = (),
        aggregates: Sequence[str] = (),
        having: DomainType = (),
        offset: int = 0,
        limit: int | None = None,
        order: str | None = None,
    ) -> list[dict]:
        """
        A method similar to :meth:`_read_group` but with all the
        formatting needed by the webclient.

        :param domain: :ref:`A search domain <reference/orm/domains>`.
            Use an empty list to match all records.
        :param groupby: list of groupby descriptions by which the
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

        :param having: A domain where the valid "fields" are the
            aggregates.

        :param offset: optional number of groups to skip

        :param limit: optional max number of groups to return

        :param order: optional ``order by`` specification, for
            overriding the natural sort ordering of the groups, see
            :meth:`~.search`.

        :return: list of dict such as
            ``[{'groupy_spec': value, ...}, ...]`` containing:

            * the groupby values: ``{groupby[i]: <value>}``
            * the aggregate values: ``{aggregates[i]: <value>}``
            * ``'__extra_domain'``: list of tuples specifying the group
              search criteria
            * ``'__fold'``: boolean if a fold_name is set on the comodel
              and read_group_expand is activated

        :raise AccessError: if user is not allowed to access requested
            information
        """
        groupby = tuple(groupby)
        aggregates = tuple(agg.replace(':recordset', ':array_agg') for agg in aggregates)

        if not order:
            order = ', '.join(groupby)

        groups = self._read_group(
            domain, groupby, aggregates,
            having=having, offset=offset, limit=limit, order=order,
        )

        # Note: group_expand is only done if the limit isn't reached and when the offset == 0
        # to avoid inconsistency in the web client pager. Anyway, in practice, this feature should
        # be used only when there are few groups (or without limit for the kanban view).
        if (
            not offset and (not limit or len(groups) < limit)
            and self._web_read_group_field_expand(groupby)
        ):
            # It doesn't respect the order with aggregates inside
            expand_groups = self._web_read_group_expand(domain, groups, groupby[0], aggregates, order)
            if not limit or len(expand_groups) <= limit:
                # Ditch the result of expand_groups because the limit is reached and to avoid
                # returning inconsistent result inside length of web_read_group
                groups = expand_groups

        fill_temporal = self.env.context.get('fill_temporal')
        if groupby and (fill_temporal or isinstance(fill_temporal, dict)):
            if limit or offset:
                raise ValueError('You cannot used fill_temporal with a limit or an offset')
            if not isinstance(fill_temporal, dict):
                fill_temporal = {}
            # This assumes that existing data is sorted by field 'groupby_name'
            groups = self._web_read_group_fill_temporal(groups, groupby, aggregates, **fill_temporal)

        return self._web_read_group_format(groupby, aggregates, groups)