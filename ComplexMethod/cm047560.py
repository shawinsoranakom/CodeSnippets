def _read_group_postprocess_aggregate(self, aggregate_spec, raw_values):
        """ Convert the given values of ``aggregate_spec``
        from PostgreSQL to the format returned by method ``_read_group()``.

        The formatting rules can be summarized as:
        - 'recordset' aggregates are turned into recordsets with a correct prefetch set;
        - NULL values are converted to empty values corresponding to the given aggregate.
        """
        empty_value = self._read_group_empty_value(aggregate_spec)

        if aggregate_spec == '__count':
            return ((value if value is not None else empty_value) for value in raw_values)

        fname, __, func = parse_read_group_spec(aggregate_spec)
        if func == 'recordset':
            field = self._fields[fname]
            Model = self.pool[field.comodel_name] if field.relational else self.pool[self._name]
            prefetch_ids = tuple(unique(
                id_
                for array_values in raw_values if array_values
                for id_ in array_values if id_
            ))

            def recordset(value):
                if not value:
                    return empty_value
                ids = tuple(unique(id_ for id_ in value if id_))
                return Model(self.env, ids, prefetch_ids)

            return (recordset(value) for value in raw_values)

        return ((value if value is not None else empty_value) for value in raw_values)