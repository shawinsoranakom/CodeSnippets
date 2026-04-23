def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Deprecated - Get the list of records in list view grouped by the given ``groupby`` fields.

        :param list domain: :ref:`A search domain <reference/orm/domains>`. Use an empty
                     list to match all records.
        :param list fields: list of fields present in the list view specified on the object.
                Each element is either 'field' (field name, using the default aggregation),
                or 'field:agg' (aggregate field with aggregation function 'agg'),
                or 'name:agg(field)' (aggregate field with 'agg' and return it as 'name').
                The possible aggregation functions are the ones provided by
                `PostgreSQL <https://www.postgresql.org/docs/current/static/functions-aggregate.html>`_
                and 'count_distinct', with the expected meaning.
        :param list groupby: list of groupby descriptions by which the records will be grouped.
                A groupby description is either a field (then it will be grouped by that field).
                For the dates an datetime fields, you can specify a granularity using the syntax 'field:granularity'.
                The supported granularities are 'hour', 'day', 'week', 'month', 'quarter' or 'year';
                Read_group also supports integer date parts:
                'year_number', 'quarter_number', 'month_number' 'iso_week_number', 'day_of_year', 'day_of_month',
                'day_of_week', 'hour_number', 'minute_number' and 'second_number'.
        :param int offset: optional number of groups to skip
        :param int limit: optional max number of groups to return
        :param str orderby: optional ``order by`` specification, for
                             overriding the natural sort ordering of the
                             groups, see also :meth:`~.search`
                             (supported only for many2one fields currently)
        :param bool lazy: if true, the results are only grouped by the first groupby and the
                remaining groupbys are put in the __context key.  If false, all the groupbys are
                done in one call.
        :return: list of dictionaries(one dictionary for each record) containing:

                    * the values of fields grouped by the fields in ``groupby`` argument
                    * __domain: list of tuples specifying the search criteria
                    * __context: dictionary with argument like ``groupby``
                    * __range: (date/datetime only) dictionary with field_name:granularity as keys
                        mapping to a dictionary with keys: "from" (inclusive) and "to" (exclusive)
                        mapping to a string representation of the temporal bounds of the group
        :rtype: [{'field_name_1': value, ...}, ...]
        :raise AccessError: if user is not allowed to access requested information
        """
        groupby = [groupby] if isinstance(groupby, str) else groupby
        lazy_groupby = groupby[:1] if lazy else groupby

        # Compatibility layer with _read_group, it should be remove in the second part of the refactoring
        # - Modify `groupby` default value 'month' into specific groupby specification
        # - Modify `fields` into aggregates specification of _read_group
        # - Modify the order to be compatible with the _read_group specification
        groupby = [groupby] if isinstance(groupby, str) else groupby
        lazy_groupby = groupby[:1] if lazy else groupby

        annotated_groupby = {}  # Key as the name in the result, value as the explicit groupby specification
        for group_spec in lazy_groupby:
            field_name, property_name, granularity = parse_read_group_spec(group_spec)
            if field_name not in self._fields:
                raise ValueError(f"Invalid field {field_name!r} on model {self._name!r}")
            field = self._fields[field_name]
            if property_name and field.type != 'properties':
                raise ValueError(f"Property name {property_name!r} has to be used on a property field.")
            if field.type in ('date', 'datetime'):
                annotated_groupby[group_spec] = f"{field_name}:{granularity or 'month'}"
            else:
                annotated_groupby[group_spec] = group_spec

        annotated_aggregates = {  # Key as the name in the result, value as the explicit aggregate specification
            f"{lazy_groupby[0].split(':')[0]}_count" if lazy and len(lazy_groupby) == 1 else '__count': '__count',
        }
        for field_spec in fields:
            if field_spec == '__count':
                continue
            match = regex_field_agg.match(field_spec)
            if not match:
                raise ValueError(f"Invalid field specification {field_spec!r}.")
            name, func, fname = match.groups()

            if fname:  # Manage this kind of specification : "field_min:min(field)"
                annotated_aggregates[name] = f"{fname}:{func}"
                continue
            if func:  # Manage this kind of specification : "field:min"
                annotated_aggregates[name] = f"{name}:{func}"
                continue

            if name not in self._fields:
                raise ValueError(f"Invalid field {name!r} on model {self._name!r}")
            field = self._fields[name]
            if field.base_field.store and field.base_field.column_type and field.aggregator and field_spec not in annotated_groupby:
                annotated_aggregates[name] = f"{name}:{field.aggregator}"

        if orderby:
            new_terms = []
            for order_term in orderby.split(','):
                order_term = order_term.strip()
                for key_name, annotated in itertools.chain(reversed(annotated_groupby.items()), annotated_aggregates.items()):
                    key_name = key_name.split(':')[0]
                    if order_term.startswith(f'{key_name} ') or key_name == order_term:
                        order_term = order_term.replace(key_name, annotated)
                        break
                new_terms.append(order_term)
            orderby = ','.join(new_terms)
        else:
            orderby = ','.join(annotated_groupby.values())

        domain = Domain(domain)
        rows = self._read_group(domain, annotated_groupby.values(), annotated_aggregates.values(), offset=offset, limit=limit, order=orderby)
        rows_dict = [
            dict(zip(itertools.chain(annotated_groupby, annotated_aggregates), row))
            for row in rows
        ]

        fill_temporal = self.env.context.get('fill_temporal')
        if lazy_groupby and (rows_dict and fill_temporal) or isinstance(fill_temporal, dict):
            # fill_temporal = {} is equivalent to fill_temporal = True
            # if fill_temporal is a dictionary and there is no data, there is a chance that we
            # want to display empty columns anyway, so we should apply the fill_temporal logic
            if not isinstance(fill_temporal, dict):
                fill_temporal = {}
            # TODO Shouldn't be possible with a limit
            rows_dict = self._read_group_fill_temporal(
                rows_dict, lazy_groupby,
                annotated_aggregates, **fill_temporal,
            )

        if lazy_groupby and lazy:
            # Right now, read_group only fill results in lazy mode (by default).
            # If you need to have the empty groups in 'eager' mode, then the
            # method _read_group_fill_results need to be completely reimplemented
            # in a sane way
            # TODO Shouldn't be possible with a limit or the limit should be in account
            rows_dict = self._read_group_fill_results(
                domain, lazy_groupby[0],
                annotated_aggregates, rows_dict, read_group_order=orderby,
            )

        for row in rows_dict:
            row['__domain'] = domain
            if len(lazy_groupby) < len(groupby):
                row['__context'] = {'group_by': groupby[len(lazy_groupby):]}

        self._read_group_format_result(rows_dict, lazy_groupby)

        return rows_dict