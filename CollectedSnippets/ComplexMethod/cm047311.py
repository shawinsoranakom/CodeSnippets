def _update_selection(self, model_name, field_name, selection):
        """ Set the selection of a field to the given list, and return the row
            values of the given selection records.
        """
        field_id = self.env['ir.model.fields']._get_ids(model_name)[field_name]

        # selection rows {value: row}
        cur_rows = self._existing_selection_data(model_name, field_name)
        new_rows = {
            value: dict(value=value, name=label, sequence=index)
            for index, (value, label) in enumerate(selection)
        }

        rows_to_insert = []
        rows_to_update = []
        rows_to_remove = []
        for value in new_rows.keys() | cur_rows.keys():
            new_row, cur_row = new_rows.get(value), cur_rows.get(value)
            if new_row is None:
                if self.pool.ready:
                    # removing a selection in the new list, at your own risks
                    _logger.warning("Removing selection value %s on %s.%s",
                                    cur_row['value'], model_name, field_name)
                    rows_to_remove.append(cur_row['id'])
            elif cur_row is None:
                new_row['name'] = Json({'en_US': new_row['name']})
                rows_to_insert.append(dict(new_row, field_id=field_id))
            elif any(new_row[key] != cur_row[key] for key in new_row):
                new_row['name'] = Json({'en_US': new_row['name']})
                rows_to_update.append(dict(new_row, id=cur_row['id']))

        if rows_to_insert:
            row_ids = query_insert(self.env.cr, self._table, rows_to_insert)
            # update cur_rows for output
            for row, row_id in zip(rows_to_insert, row_ids):
                cur_rows[row['value']] = dict(row, id=row_id)

        for row in rows_to_update:
            query_update(self.env.cr, self._table, row, ['id'])

        if rows_to_remove:
            self.browse(rows_to_remove).unlink()

        return cur_rows