def web_read_group(
        self,
        domain: DomainType,
        groupby: list[str] | tuple[str, ...],
        aggregates: Sequence[str] = (),
        limit: int | None = None,
        offset: int = 0,
        order: str | None = None,
        *,
        auto_unfold: bool = False,
        opening_info: list[dict] | None = None,
        unfold_read_specification: dict[str, dict] | None = None,
        unfold_read_default_limit: int | None = 80,  # Limit of record by unfolded group by default
        groupby_read_specification: dict[str, dict] | None = None,
    ) -> dict[str, int | list]:
        """
        Serves as the primary method for loading grouped data in list and kanban views.

        This method wraps :meth:`~.formatted_read_group` to return both the grouped
        data and the total number of groups matching the search domain. It also
        conditionally opens (unfolds) groups based on the `auto_unfold` parameter
        and the `__fold` key returned by :meth:`~.formatted_read_group`.

        A group is considered "open" if it contains a `__records` or `__groups` key.
        - `__records`: The result of a :meth:`~.web_search_read` call for the group.
        - `__groups`: The results of subgroupings.

        :param domain: :ref:`A search domain <reference/orm/domains>`.
        :param groupby: A list of groupby specification at each level, see :meth:`~.formatted_read_group`.
        :param aggregates: A list of aggregate specifications. see :meth:`~.formatted_read_group`
        :param limit: The maximum number of top-level groups to return. see :meth:`~.formatted_read_group`
        :param offset: The offset for the top-level groups. see :meth:`~.formatted_read_group`
        :param order: A sort string, as used in :meth:`~.search`
        :param auto_unfold: If `True`, automatically unfolds the first 10 groups according to their
            `__fold` key, if present; otherwise, it is unfolded by default.
            This is typically `True` for kanban views and `False` for list views.
        :param opening_info: The state of currently opened groups, used for reloading.
          ::

            opening_info = [{
                "value": raw_value_groupby,
                "folded": True or False,
                ["offset": int,]  # present if unfolded
                ["limit": int,]  # present if unfolded
                ["progressbar_domain": progressbar_domain,]  # present if unfolded, e.g., when clicking on a progress bar section
                ["groups": <opening_info>,]  # present if unfolded
            }]

        :param unfold_read_specification: The read specification for :meth:`~.web_read` when unfolding a group.
        :param unfold_read_default_limit: The default record limit to apply when unfolding a group.
        :param groupby_read_specification: The :meth:`~.web_read` specification for reading the records
            that are being grouped on. This is mainly for list views with <groupby> leaves.
            {<groupby_spec>: <read_specification>}

        :return: A dictionary with the following structure:
          ::

            {
                'groups': <groups>,
                'length': <total_group_count>,
            }

            Where <groups> is the result of :meth:`~.formatted_read_group`, but with an
            added `__groups` key for subgroups or a `__records` key for the result of :meth:`~.web_read`
            for records within the group.

        """
        assert isinstance(groupby, (list, tuple)) and groupby

        aggregates = list(aggregates)
        if '__count' not in aggregates:  # Used for computing length of sublevel groups
            aggregates.append('__count')
        domain = Domain(domain).optimize(self)

        # dict to help creating order compatible with _read_group and for search
        dict_order: dict[str, str] = {}  # {fname_and_property: "<direction> <nulls>"}
        for order_part in (order.split(',') if order else ()):
            order_match = regex_order.match(order_part)
            if not order_match:
                raise ValueError(f"Invalid order {order!r} for web_read_group()")
            fname_and_property = order_match['field']
            if order_match['property']:
                fname_and_property = f"{fname_and_property}.{order_match['property']}"
            direction = (order_match['direction'] or 'ASC').upper()
            if order_match['nulls']:
                direction = f"{direction} {order_match['nulls'].upper()}"
            dict_order[fname_and_property] = direction

        # First level of grouping
        first_groupby = [groupby[0]]
        read_group_order = self._get_read_group_order(dict_order, first_groupby, aggregates)
        groups, length = self._formatted_read_group_with_length(
            domain, first_groupby, aggregates, offset=offset, limit=limit, order=read_group_order,
        )

        # Open sublevel of grouping (list) and get all subgroup to open into records.
        # [{limit: int, offset: int, domain: domain, group: <group>}]
        records_opening_info: list[dict[str, Any]] = []

        self._open_groups(
            records_opening_info=records_opening_info,
            groups=groups,
            domain=domain,
            groupby=groupby,
            aggregates=aggregates,
            dict_order=dict_order,
            auto_unfold=auto_unfold,
            opening_info=opening_info,
            unfold_read_default_limit=unfold_read_default_limit,
            parent_opening_info=opening_info,
            parent_group_domain=Domain.TRUE,
        )

        # Open last level of grouping, meaning read records of groups
        if records_opening_info:

            order_specs = [
                f"{fname} {direction}"
                for fname, direction in dict_order.items()
                # Remove order that are already unique for each group,
                # that may avoid a left join and simplify the order (not apply if granularity)
                if fname not in groupby
                if fname != '__count'
            ]
            for order_str in self._order.split(','):
                fname = order_str.strip().split(" ", 1)[0]
                if fname not in dict_order and fname not in groupby:
                    order_specs.append(order_str)

            order_searches = ', '.join(order_specs)
            recordset_groups = [
                self.search(
                    domain & sub_search['domain'],
                    order=order_searches,
                    limit=sub_search['limit'],
                    offset=sub_search['offset'],
                ) if sub_search['group']['__count'] else self.browse()
                for sub_search in records_opening_info
            ]

            all_records = self.browse().union(*recordset_groups)
            record_mapped = dict(zip(
                all_records._ids,
                all_records.web_read(unfold_read_specification or {}),
                strict=True,
            ))

            for opening, records in zip(records_opening_info, recordset_groups, strict=True):
                opening['group']['__records'] = [record_mapped[record_id] for record_id in records._ids]

        # Read additional info of grouped field record and add it to specific groups
        self._add_groupby_values(groupby_read_specification, groupby, groups)

        return {
            'groups': groups,
            'length': length,
        }