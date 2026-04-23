def _read_group_postprocess_groupby(self, groupby_spec, raw_values):
        """ Convert the given values of ``groupby_spec``
        from PostgreSQL to the format returned by method ``_read_group()``.

        The formatting rules can be summarized as:
        - groupby values of relational fields are converted to recordsets with a correct prefetch set;
        - NULL values are converted to empty values corresponding to the given aggregate.
        """
        empty_value = self._read_group_empty_value(groupby_spec)

        fname, chain_fnames, granularity = parse_read_group_spec(groupby_spec)
        field = self._fields[fname]

        if field.relational or fname == 'id':
            if chain_fnames and field.relational:
                groupby_seq = f"{chain_fnames}:{granularity}" if granularity else chain_fnames
                model = self.env[field.comodel_name]
                return model._read_group_postprocess_groupby(groupby_seq, raw_values)

            Model = self.pool[field.comodel_name] if field.relational else self.pool[self._name]
            prefetch_ids = tuple(raw_value for raw_value in raw_values if raw_value)

            def recordset(value):
                return Model(self.env, (value,), prefetch_ids) if value else empty_value

            return (recordset(value) for value in raw_values)

        return ((value if value is not None else empty_value) for value in raw_values)