def _add_groupby_values(self, groupby_read_specification: dict[str, dict] | None, groupby: list[str], current_groups: list):
        if not groupby_read_specification or groupby_read_specification.keys().isdisjoint(groupby):
            return

        for groupby_spec in groupby:
            if groupby_spec in groupby_read_specification:
                relational_field = self._fields[groupby_spec]
                assert relational_field.comodel_name, "We can only read extra info from a relational field"
                group_ids = [
                    id_label[0] for group in current_groups if (id_label := group[groupby_spec])
                ]
                records = self.env[relational_field.comodel_name].browse(group_ids)

                result_read = records.web_read(groupby_read_specification[groupby_spec])
                result_read_map = dict(zip(records._ids, result_read, strict=True))
                for group in current_groups:
                    id_label = group[groupby_spec]
                    group['__values'] = result_read_map[id_label[0]] if id_label else {'id': False}

            current_groups = [
                subgroup
                for group in current_groups
                for subgroup in group.get('__groups', {}).get('groups', ())
            ]