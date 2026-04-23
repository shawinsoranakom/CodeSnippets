def _read_group_fill_results(self, domain, groupby, annoted_aggregates, read_group_result, read_group_order=None):
        """Helper method for filling in empty groups for all possible values of
           the field being grouped by"""
        field_name = groupby.split('.')[0].split(':')[0]
        field = self._fields[field_name]
        if not field or not field.group_expand:
            return read_group_result

        # field.group_expand is a callable or the name of a method, that returns
        # the groups that we want to display for this field, in the form of a
        # recordset or a list of values (depending on the type of the field).
        # This is useful to implement kanban views for instance, where some
        # columns should be displayed even if they don't contain any record.
        group_expand = field.group_expand
        if isinstance(group_expand, str):
            group_expand = getattr(self.env.registry[self._name], group_expand)
        assert callable(group_expand)

        # determine all groups that should be returned
        values = [line[groupby] for line in read_group_result if line[groupby]]

        if field.relational:
            # groups is a recordset; determine order on groups's model
            groups = self.env[field.comodel_name].browse(value.id for value in values)
            values = group_expand(self, groups, domain).sudo()
            if read_group_order == groupby + ' desc':
                values.browse(reversed(values._ids))
            value2key = lambda value: value and value.id

        else:
            # groups is a list of values
            values = group_expand(self, values, domain)
            if read_group_order == groupby + ' desc':
                values.reverse()
            value2key = lambda value: value

        # Merge the current results (list of dicts) with all groups. Determine
        # the global order of results groups, which is supposed to be in the
        # same order as read_group_result (in the case of a many2one field).

        read_group_result_as_dict = {}
        for line in read_group_result:
            read_group_result_as_dict[value2key(line[groupby])] = line

        empty_item = {
            name: self._read_group_empty_value(spec)
            for name, spec in annoted_aggregates.items()
        }

        result = {}
        # fill result with the values order
        for value in values:
            key = value2key(value)
            if key in read_group_result_as_dict:
                result[key] = read_group_result_as_dict.pop(key)
            else:
                result[key] = dict(empty_item, **{groupby: value})

        for line in read_group_result_as_dict.values():
            key = value2key(line[groupby])
            result[key] = line

        # add folding information if present
        if field.relational and groups._fold_name in groups._fields:
            fold = {group.id: group[groups._fold_name]
                    for group in groups.browse(key for key in result if key)}
            for key, line in result.items():
                line['__fold'] = fold.get(key, False)

        return list(result.values())