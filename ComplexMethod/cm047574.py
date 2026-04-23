def _read_format(self, fnames: Sequence[str], load: str = '_classic_read') -> list[ValuesType]:
        """Return a list of dictionaries mapping field names to their values,
        with one dictionary per record that exists.

        The output format is the one expected from the `read` method, which uses
        this method as its implementation for formatting values.

        For the properties fields, call convert_to_read_multi instead of convert_to_read
        to prepare everything (record existences, display name, etc) in batch.

        The current method is different from `read` because it retrieves its
        values from the cache without doing a query when it is avoidable.
        """
        data = [(record, {'id': record.id}) for record in self]
        use_display_name = (load == '_classic_read')
        for name in fnames:
            field = self._fields[name]
            if field.type == 'properties':
                values_list = []
                records = []
                for record, vals in data:
                    try:
                        values_list.append(record[name])
                        records.append(record.id)
                    except MissingError:
                        vals.clear()

                results = field.convert_to_read_multi(values_list, self.browse(records))
                for record_read_vals, convert_result in zip(data, results):
                    record_read_vals[1][name] = convert_result
                continue

            convert = field.convert_to_read
            for record, vals in data:
                # missing records have their vals empty
                if not vals:
                    continue
                try:
                    vals[name] = convert(record[name], record, use_display_name)
                except MissingError:
                    vals.clear()
        result = [vals for record, vals in data if vals]

        return result