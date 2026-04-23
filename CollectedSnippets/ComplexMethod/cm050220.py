def _read_grouping_sets(self, domain, grouping_sets, aggregates=(), order=None):
        if self._SPECIAL_SUM_AGGREGATES.isdisjoint(aggregates):
            return super()._read_grouping_sets(domain, grouping_sets, aggregates, order)

        base_aggregates = [*(agg for agg in aggregates if agg not in self._SPECIAL_SUM_AGGREGATES), 'id:recordset']
        base_result = super()._read_grouping_sets(domain, grouping_sets, base_aggregates, order)

        # Force the compute of all records to bypass the limit compute batching (PREFETCH_MAX)
        all_records = self.concat(*(item[-1] for row in base_result for item in row))
        # This line will compute all fields having _compute_product_margin_fields_values
        # as compute method.
        all_records._compute_product_margin_fields_values()

        # base_result = [[(a1, b1, records), (a2, b2, records), ...], [(a1, b1, c1, records), (a2, b2, c2, records), ...] ...]
        result = []
        for grouping_spec, grouping in zip(grouping_sets, base_result):
            row = []
            for *other, records in grouping:
                for index, spec in enumerate(itertools.chain(grouping_spec, aggregates)):
                    if spec in self._SPECIAL_SUM_AGGREGATES:
                        field_name = spec.split(':')[0]
                        other.insert(index, sum(records.mapped(field_name)))
                row.append(tuple(other))
            result.append(row)

        return result