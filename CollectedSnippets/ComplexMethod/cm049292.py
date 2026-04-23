def _web_read_group_expand(self, domain, groups, groupby_spec, aggregates, order):
        """ Expand the result of _read_group for the webclient to show empty groups
        for some view types (e.g. empty column for kanban view). See `Field.group_expand` attribute.
        """
        field_name = groupby_spec.split('.')[0].split(':')[0]
        field = self._fields[field_name]

        # determine all groups that should be returned
        values = [group_value for group_value, *__ in groups if group_value]

        # field.group_expand is a callable or the name of a method, that returns
        # the groups that we want to display for this field, in the form of a
        # recordset or a list of values (depending on the type of the field).
        # This is useful to implement kanban views for instance, where some
        # columns should be displayed even if they don't contain any record.
        if field.relational:
            # groups is a recordset; determine order on groups's model
            values = self.env[field.comodel_name].browse(value.id for value in values)
            expand_values = field.determine_group_expand(self, values, domain)
            all_record_ids = tuple(unique(expand_values._ids + values._ids))
        else:
            # groups is a list of values
            expand_values = field.determine_group_expand(self, values, domain)

        if (groupby_spec + ' desc') in order.lower():
            expand_values = reversed(expand_values)

        empty_aggregates = tuple(self._read_group_empty_value(spec) for spec in aggregates)
        result = dict.fromkeys(expand_values, empty_aggregates)
        result.update({
            group_value: aggregate_values
            for group_value, *aggregate_values in groups
        })

        if field.relational:
            return [
                (value.with_prefetch(all_record_ids), *aggregate_values)
                for value, aggregate_values in result.items()
            ]
        return [(value, *aggregate_values) for value, aggregate_values in result.items()]