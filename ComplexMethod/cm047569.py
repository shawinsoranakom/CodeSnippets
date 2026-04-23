def _auto_init(self) -> None:
        """ Initialize the database schema of ``self``:
            - create the corresponding table,
            - create/update the necessary columns/tables for fields,
            - initialize new columns on existing rows,
            - add the SQL constraints given on the model,
            - add the indexes on indexed fields,

            Also prepare post-init stuff to:
            - add foreign key constraints,
            - reflect models, fields, relations and constraints,
            - mark fields to recompute on existing records.

            Note: you should not override this method. Instead, you can modify
            the model's database schema by overriding method :meth:`~.init`,
            which is called right after this one.
        """
        raise_on_invalid_object_name(self._name)

        # This prevents anything called by this method (in particular default
        # values) from prefetching a field for which the corresponding column
        # has not been added in database yet!
        self = self.with_context(prefetch_fields=False)

        cr = self.env.cr
        update_custom_fields = self.env.context.get('update_custom_fields', False)
        must_create_table = not sql.table_exists(cr, self._table)
        parent_path_compute = False

        if self._auto:
            if must_create_table:
                def make_type(field):
                    return field.column_type[1] + (" NOT NULL" if field.required else "")

                sql.create_model_table(cr, self._table, self._description, [
                    (field.name, make_type(field), field.string)
                    for field in sorted(self._fields.values(), key=lambda f: f.column_order)
                    if field.name != 'id' and field.store and field.column_type
                ])

            if self._parent_store:
                if not sql.column_exists(cr, self._table, 'parent_path'):
                    sql.create_column(self.env.cr, self._table, 'parent_path', 'VARCHAR')
                    parent_path_compute = True
                self._check_parent_path()

            if not must_create_table:
                self._check_removed_columns(log=False)

            # update the database schema for fields
            columns = sql.table_columns(cr, self._table)
            fields_to_compute = []

            for field in sorted(self._fields.values(), key=lambda f: f.column_order):
                if not field.store:
                    continue
                if field.manual and not update_custom_fields:
                    continue            # don't update custom fields
                new = field.update_db(self, columns)
                if new and field.compute:
                    fields_to_compute.append(field)

            if fields_to_compute:
                # mark existing records for computation now, so that computed
                # required fields are flushed before the NOT NULL constraint is
                # added to the database
                cr.execute(SQL('SELECT id FROM %s', SQL.identifier(self._table)))
                records = self.browse(row[0] for row in cr.fetchall())
                if records:
                    for field in fields_to_compute:
                        _logger.info("Prepare computation of %s", field)
                        self.env.add_to_compute(field, records)

        if self._auto:
            self._add_sql_constraints()

        if parent_path_compute:
            self._parent_store_compute()