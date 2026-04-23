def update_db_notnull(self, model: BaseModel, column: dict[str, typing.Any]):
        """ Add or remove the NOT NULL constraint on ``self``.

            :param model: an instance of the field's model
            :param column: the column's configuration (dict) if it exists, or ``None``
        """
        has_notnull = column and column['is_nullable'] == 'NO'

        if not column or (self.required and not has_notnull):
            # the column is new or it becomes required; initialize its values
            if model._table_has_rows():
                model._init_column(self.name)

        if self.required and not has_notnull:
            # _init_column may delay computations in post-init phase
            @model.pool.post_init
            def add_not_null():
                # At the time this function is called, the model's _fields may have been reset, although
                # the model's class is still the same. Retrieve the field to see whether the NOT NULL
                # constraint still applies.
                field = model._fields[self.name]
                if not field.required or not field.store:
                    return
                if field.compute:
                    records = model.browse(id_ for id_, in model.env.execute_query(SQL(
                        "SELECT id FROM %s AS t WHERE %s IS NULL",
                        SQL.identifier(model._table), model._field_to_sql('t', field.name),
                    )))
                    model.env.add_to_compute(field, records)
                # Flush values before adding NOT NULL constraint.
                model.flush_model([field.name])
                model.pool.post_constraint(
                    model.env.cr,
                    lambda cr: sql.set_not_null(cr, model._table, field.name),
                    key=f"add_not_null:{model._table}:{field.name}",
                )

        elif not self.required and has_notnull:
            sql.drop_not_null(model.env.cr, model._table, self.name)