def _web_read_group_format(
        self,
        groupby: tuple[str, ...],
        aggregates: tuple[str, ...],
        groups: list[tuple],
    ) -> list[dict]:
        """ Format raw value of _read_group for the webclient.
        See formatted_read_group return value. """
        result = [{'__extra_domains': []} for __ in groups]
        if not groups:
            return result
        column_iterator = zip(*groups)

        for groupby_spec, values in zip(groupby, column_iterator):
            formatter = self._web_read_group_groupby_formatter(groupby_spec, values)
            for value, dict_group in zip(values, result, strict=True):
                dict_group[groupby_spec], additional_domain = formatter(value)
                dict_group['__extra_domains'].append(additional_domain)

            # Add fold information only if read_group_expand is activated (for kanban/list)
            if ((field := self._web_read_group_field_expand(groupby)) and field.relational):
                model = self.env[field.comodel_name]
                fold_name = model._fold_name
                if fold_name not in model._fields:
                    continue
                for value, dict_group in zip(values, result):
                    dict_group['__fold'] = value.sudo()[fold_name]

        # Reconstruct groups domain part
        for dict_group in result:
            dict_group['__extra_domain'] = AND(dict_group.pop('__extra_domains'))

        for aggregate_spec, values in zip(aggregates, column_iterator, strict=True):
            for value, dict_group in zip(values, result, strict=True):
                dict_group[aggregate_spec] = value

        return result