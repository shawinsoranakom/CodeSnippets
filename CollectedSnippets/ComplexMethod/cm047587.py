def _clean_properties(self) -> None:
        """ Remove all properties of ``self`` that are no longer in the related definition """
        for fname, field in self._fields.items():
            if field.type != 'properties':
                continue
            for record in self:
                old_value = record[fname]._values
                if not old_value:
                    continue

                definitions = field._get_properties_definition(record)
                all_names = {definition['name'] for definition in definitions}
                new_values = {name: value for name, value in old_value.items() if name in all_names}
                if len(new_values) != len(old_value):
                    record[fname] = new_values