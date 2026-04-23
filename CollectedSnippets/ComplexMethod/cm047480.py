def update_db(self, model: BaseModel, columns: dict[str, dict[str, typing.Any]]) -> bool:
        """ Update the database schema to implement this field.

            :param model: an instance of the field's model
            :param columns: a dict mapping column names to their configuration in database
            :return: ``True`` if the field must be recomputed on existing rows
        """
        if not self.column_type:
            return False

        column = columns.get(self.name)

        # create/update the column, not null constraint; the index will be
        # managed by registry.check_indexes()
        self.update_db_column(model, column)
        self.update_db_notnull(model, column)

        # optimization for computing simple related fields like 'foo_id.bar'
        if (
            not column
            and self.related and self.related.count('.') == 1
            and self.related_field.store and not self.related_field.compute
            and not (self.related_field.type == 'binary' and self.related_field.attachment)
            and self.related_field.type not in ('one2many', 'many2many')
        ):
            join_field = model._fields[self.related.split('.')[0]]
            if (
                join_field.type == 'many2one'
                and join_field.store and not join_field.compute
            ):
                model.pool.post_init(self.update_db_related, model)
                # discard the "classical" computation
                return False

        return not column