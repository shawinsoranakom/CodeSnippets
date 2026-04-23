def _str_to_many2many(self, model, field, value, savepoint):
        [record] = value

        subfield, warnings = self._referencing_subfield(record)

        ids = []
        for reference in record[subfield].split(','):
            id, ws = self.db_id_for(model, field, subfield, reference, savepoint)
            ids.append(id)
            warnings.extend(ws)

        if field.name in self.env.context.get('import_set_empty_fields', []) and any(id is None for id in ids):
            ids = [id for id in ids if id]
        elif field.name in self.env.context.get('import_skip_records', []) and any(id is None for id in ids):
            return None, warnings

        if self.env.context.get('update_many2many'):
            return [Command.link(id) for id in ids], warnings
        else:
            return [Command.set(ids)], warnings