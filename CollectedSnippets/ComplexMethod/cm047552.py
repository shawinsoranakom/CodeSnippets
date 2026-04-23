def _read_grouping_sets(
        self,
        domain: DomainType,
        grouping_sets: Sequence[Sequence[str]],
        aggregates: Sequence[str] = (),
        order: str | None = None,
    ) -> list[list[tuple]]:
        """ Performs multiple aggregations with different groupings in a single query if possible.

        This method uses SQL `GROUPING SETS` as a more advanced and efficient
        alternative to calling :meth:`~._read_group` multiple times with different
        `groupby` parameters. It allows you to get different levels of aggregated
        data in one database round-trip.
        Note that for many2many multiple SQL might be needed because of the deduplicated rows.

        :param domain: :ref:`A search domain <reference/orm/domains>` to filter records before grouping
        :param grouping_sets: A list of `groupby` specifications. Each inner list
                              is a set of fields to group by and is equivalent to the
                              `groupby` parameter of the :meth:`~._read_group` method.
                              For example: `[['partner_id'], ['partner_id', 'state']]`.
        :param aggregates: list of aggregates specification.
                Each element is `'field:agg'` (aggregate field with aggregation function `'agg'`).
                The possible aggregation functions are the ones provided by
                `PostgreSQL <https://www.postgresql.org/docs/current/static/functions-aggregate.html>`_,
                `'count_distinct'` with the expected meaning and `'recordset'` to act like `'array_agg'`
                converted into a recordset.
        :param order: optional ``order by`` specification, for
                overriding the natural sort ordering of the groups,
                see also :meth:`~.search`.
        :return: A list of lists of tuples. The outer list's structure mirrors the
                 input `grouping_sets`. Each inner list contains the results for one
                 grouping specification. Each tuple within an inner list contains the
                 values for the grouped fields, followed by the aggregate values,
                 in the order they were specified.

                 For example, given:
                 - `grouping_sets=[['foo'], ['foo', 'bar']]`
                 - `aggregates=['baz:sum']`

                 The returned structure would be:
                  ::

                    [
                        # Results for ['foo']
                        [(foo1_val, baz_sum_1), (foo2_val, baz_sum_2), ...],
                        # Results for ['foo', 'bar']
                        [(foo1_val, bar1_val, baz_sum_3), (foo2_val, bar2_val, baz_sum_4), ...],
                    ]

        :raise AccessError: if user is not allowed to access requested information
        """
        if not grouping_sets:
            raise ValueError("The 'grouping_sets' parameter cannot be empty.")

        query = self._search(domain)
        result = [[] for __ in grouping_sets]
        if query.is_empty():
            return result

        # grouping_sets: [(a, b), (a), ()]
        # all_groupby_specs: (a, b)
        all_groupby_specs = tuple(unique(spec for groupby in grouping_sets for spec in groupby))

        # --- Many2many Special Handling ---
        many2many_groupby_specs = []
        if len(grouping_sets) > 1:  # many2many logic only applies if we have multiple groupings

            def might_duplicate_rows(model, spec) -> bool:
                fname, property_name, __ = parse_read_group_spec(spec)
                field = model._fields[fname]
                if field.type == 'properties':
                    definition = self.get_property_definition(f"{fname}.{property_name}")
                    property_type = definition.get('type')
                    return property_type in ('tags', 'many2many')

                if property_name:
                    assert field.type == 'many2one'
                    return might_duplicate_rows(self.env[field.comodel_name], property_name)

                return field.type == 'many2many'

            for spec in all_groupby_specs:
                if might_duplicate_rows(self, spec):
                    many2many_groupby_specs.append(spec)

        if (
            many2many_groupby_specs and
            # If aggregates are sensitive to row duplication (like sum, avg), we must isolate M2M groupings.
            any(
                not aggregate.endswith(
                    (':max', ':min', ':bool_and', ':bool_or', ':array_agg_distinct', ':recordset', ':count_distinct'),
                )
                for aggregate in aggregates if aggregate != '__count'
            )
        ):
            # The following logic is a recursive decomposition strategy. It's complex
            # but necessary to prevent M2M joins from corrupting aggregates in other grouping sets.
            # We find all combinations of M2M fields and create a sub-call for grouping sets
            # that share that exact combination of M2M fields.

            # ['A', 'B', 'C'] => [('A', 'B', 'C'), ('A', 'B'), ('A', 'C'), ('B', 'C'), ('A',), ('B',), ('C',), ()]
            m2m_combinaisons = (
                groupby for i in range(len(many2many_groupby_specs), -1, -1)
                for groupby in itertools.combinations(many2many_groupby_specs, i)
            )

            grouping_sets_to_process = dict(enumerate(grouping_sets))
            batched_calls = []  # [([groupby, ...], [index_result, ...])]

            for m2m_comb in m2m_combinaisons:
                if not grouping_sets_to_process:
                    break
                sub_grouping_sets = []
                sub_result_indexes = []
                for i, groupby in list(grouping_sets_to_process.items()):
                    if all(m2m in groupby for m2m in m2m_comb):
                        sub_grouping_sets.append(groupby)
                        sub_result_indexes.append(i)
                        grouping_sets_to_process.pop(i)

                if sub_grouping_sets:
                    batched_calls.append((sub_result_indexes, sub_grouping_sets))

            assert not grouping_sets_to_process
            # If the problem was decomposed, make recursive calls and assemble results.
            if len(batched_calls) > 1:
                for indexes, sub_grouping_sets in batched_calls:

                    sub_order_parts = []
                    all_sub_groupby = {spec for groupby in sub_grouping_sets for spec in groupby}
                    for order_part in (order or '').split(','):
                        order_part = order_part.strip()
                        if not any(
                            order_part.startswith(spec)
                            for spec in all_groupby_specs if spec not in all_sub_groupby
                        ):
                            sub_order_parts.append(order_part)

                    sub_results = self._read_grouping_sets(
                        domain, sub_grouping_sets, aggregates=aggregates, order=",".join(sub_order_parts),
                    )
                    for index, subresult in zip(indexes, sub_results):
                        result[index] = subresult
                return result

        elif many2many_groupby_specs and '__count' in aggregates:
            # Efficiently handle '__count' with M2M fields by using a distinct count on 'id'
            # without making another _read_grouping_sets (this is the very common case).
            aggregates = tuple(
                aggregate if aggregate != '__count' else 'id:count_distinct'
                for aggregate in aggregates
            )
            if order:
                order = order.replace('__count', 'id:count_distinct')

        # --- SQL Query Construction ---
        groupby_terms: dict[str, SQL] = {
            spec: self._read_group_groupby(self._table, spec, query) for spec in all_groupby_specs
        }
        aggregates_terms: list[SQL] = [
            self._read_group_select(spec, query) for spec in aggregates
        ]
        if groupby_terms:
            # grouping_select_sql: GROUPING(a, b)
            grouping_select_sql = SQL("GROUPING(%s)", SQL(", ").join(unique(groupby_terms.values())))
        else:
            # GROUPING() is invalid SQL, so we use the 0 as literal
            grouping_select_sql = SQL("0")

        select_args = [grouping_select_sql, *groupby_terms.values(), *aggregates_terms]

        # _read_group_orderby may change groupby_terms then it is necessary to be call before
        query.order = self._read_group_orderby(order, groupby_terms, query)
        # GROUPING SET ((a, b), (a), ())
        grouping_sets_sql = [
            SQL("(%s)", SQL(", ").join(groupby_terms[groupby_spec] for groupby_spec in grouping_set))
            for grouping_set in grouping_sets
        ]
        query.groupby = SQL("GROUPING SETS (%s)", SQL(", ").join(unique(grouping_sets_sql)))

        # This handles the case where `order` adds columns that must also be in `GROUP BY`.
        # Rebuild the grouping sets to include these extra terms.

        # row_values: [(GROUPING(...), a1, b1, aggregates...), (GROUPING(...), a2, b2, aggregates...), ...]
        row_values = self.env.execute_query(query.select(*select_args))

        if not row_values:  # shortcut
            return result

        # --- Result Post-Processing ---
        # This is the core of the result dispatching logic. It uses the integer
        # returned by GROUPING() as a key to map each result row to the correct
        # grouping set defined by the user.
        aggregates_indexes = tuple(range(len(all_groupby_specs), len(all_groupby_specs) + len(aggregates)))

        # Map each possible GROUPING() bitmask to its corresponding result list and value extractor.
        # {GROUPING(...): (append_method, extractor_method)}
        mask_grouping_mapping = {}

        # Create a mapping from each unique SQL GROUP BY term to its bitmask value.
        # The terms are reversed to match the PostgreSQL logic where the bitmask was
        # calculated from right to left (LSB first).
        # See PostgreSQL Doc: https://www.postgresql.org/docs/17/functions-aggregate.html#Grouping-Operations
        mask_sql_mapping = {
            sql_groupby: 1 << i
            for i, sql_groupby in enumerate(unique(reversed(groupby_terms.values())))
        }

        mask_grouping_result_indexes = defaultdict(list)  # To manage "duplicated" groupby
        for result_index, groupby in enumerate(grouping_sets):
            # E.g. GROUPING SET ((a, b), (a), ())
            # GROUPING(a, b): a and b included = 0, a included = 1, b included = 2, none included = 3
            sql_terms = {groupby_terms[groupby_spec] for groupby_spec in groupby}
            groupby_mask = sum(
                mask for sql_term, mask in mask_sql_mapping.items()
                # each bit is 0 if the corresponding expression is included in the grouping criteria
                # of the grouping set generating the current result row, and 1 if it is not included.
                if sql_term not in sql_terms
            )

            mask_grouping_result_indexes[groupby_mask].append(result_index)
            if groupby_mask not in mask_grouping_mapping:
                mask_grouping_mapping[groupby_mask] = (
                    result[result_index].append,
                    itemgetter_tuple(list(itertools.chain(
                        (all_groupby_specs.index(groupby_spec) for groupby_spec in groupby),
                        aggregates_indexes,
                    ))),
                )

        aggregates_start_index = len(all_groupby_specs) + 1
        # Transpose rows to columns for efficient, column-wise post-processing.
        columns = list(zip(*row_values))
        # The first column is the grouping mask
        dispatch_info = map(mask_grouping_mapping.__getitem__, columns[0])
        # Post-process values column by column
        columns = [
            *map(self._read_group_postprocess_groupby, all_groupby_specs, columns[1:aggregates_start_index]),
            *map(self._read_group_postprocess_aggregate, aggregates, columns[aggregates_start_index:]),
        ]

        # result: [
        #   [(a1, b1, <aggregates>), (a2, b2, <aggregates>), ...],
        #   [(a1, <aggregates>), (a2, <aggregates>), ...],
        #   [(<aggregates>)],
        # ]
        for (append_method, extractor), *row in zip(dispatch_info, *columns, strict=True):
            append_method(extractor(row))

        # Manage groupbys targetting the same column(s), then having the same results
        for duplicate_groups_indexes in mask_grouping_result_indexes.values():
            if len(duplicate_groups_indexes) < 2:
                continue
            # The first index's result is the source for all others in this group
            source_result_group = result[duplicate_groups_indexes[0]]
            for duplicate_group_index in duplicate_groups_indexes[1:]:
                result[duplicate_group_index] = source_result_group[:]

        return result