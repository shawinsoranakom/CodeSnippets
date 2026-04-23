def _reflect_fields(self, model_names):
        super()._reflect_fields(model_names)

        # set 'serialization_field_id' on sparse fields; it is done here to
        # ensure that the serialized field is reflected already
        cr = self.env.cr

        # retrieve existing values
        query = """
            SELECT model, name, id, serialization_field_id
            FROM ir_model_fields
            WHERE model IN %s
        """
        cr.execute(query, [tuple(model_names)])
        existing = {row[:2]: row[2:] for row in cr.fetchall()}

        # determine updates, grouped by value
        updates = defaultdict(list)
        for model_name in model_names:
            for field_name, field in self.env[model_name]._fields.items():
                field_id, current_value = existing[(model_name, field_name)]
                try:
                    value = existing[(model_name, field.sparse)][0] if field.sparse else None
                except KeyError:
                    raise UserError(_(
                        'Serialization field "%(serialization_field)s" not found for sparse field %(sparse_field)s!',
                        serialization_field=field.sparse,
                        sparse_field=field,
                    ))
                if current_value != value:
                    updates[value].append(field_id)

        if not updates:
            return

        # update fields
        query = "UPDATE ir_model_fields SET serialization_field_id=%s WHERE id IN %s"
        for value, ids in updates.items():
            cr.execute(query, [value, tuple(ids)])

        records = self.browse(id_ for ids in updates.values() for id_ in ids)
        self.pool.post_init(records.modified, ['serialization_field_id'])