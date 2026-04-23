def convert_to_read_multi(self, values, records, use_display_name=True):
        if not records:
            return values
        assert len(values) == len(records)

        # each value is either False or a dict
        result = []
        for record, value in zip(records, values):
            value = value._values if isinstance(value, Property) else value  # Property -> dict
            if definition := self._get_properties_definition(record):
                value = value or {}
                assert isinstance(value, dict), f"Wrong type {value!r}"
                result.append(self._dict_to_list(value, definition))
            else:
                result.append([])

        res_ids_per_model = self._get_res_ids_per_model(records.env, result)

        # value is in record format
        for value in result:
            self._parse_json_types(value, records.env, res_ids_per_model)

        if use_display_name:
            for value in result:
                self._add_display_name(value, records.env)

        return result