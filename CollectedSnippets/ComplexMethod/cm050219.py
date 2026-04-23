def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        """
            Inherit _read_group to calculate the sum of the non-stored fields, as it is not automatically done anymore through the XML.
        """
        if self._SPECIAL_SUM_AGGREGATES.isdisjoint(aggregates):
            return super()._read_group(domain, groupby, aggregates, having, offset, limit, order)

        base_aggregates = [*(agg for agg in aggregates if agg not in self._SPECIAL_SUM_AGGREGATES), 'id:recordset']
        base_result = super()._read_group(domain, groupby, base_aggregates, having, offset, limit, order)

        # Force the compute of all records to bypass the limit compute batching (PREFETCH_MAX)
        all_records = self.browse().union(*(item[-1] for item in base_result))
        # This line will compute all fields having _compute_product_margin_fields_values
        # as compute method.
        self._fields['turnover'].compute_value(all_records)

        # base_result = [(a1, b1, records), (a2, b2, records), ...]
        result = []
        for *other, records in base_result:
            for index, spec in enumerate(itertools.chain(groupby, aggregates)):
                if spec in self._SPECIAL_SUM_AGGREGATES:
                    field_name = spec.split(':')[0]
                    other.insert(index, sum(records.mapped(field_name)))
            result.append(tuple(other))

        return result