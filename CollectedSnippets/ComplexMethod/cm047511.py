def check_null_constraints(self, cr: Cursor) -> None:
        """ Check that all not-null constraints are set. """
        cr.execute('''
            SELECT c.relname, a.attname
            FROM pg_attribute a
            JOIN pg_class c ON a.attrelid = c.oid
            WHERE c.relnamespace = current_schema::regnamespace
            AND a.attnotnull = true
            AND a.attnum > 0
            AND a.attname != 'id';
        ''')
        not_null_columns = set(cr.fetchall())

        self.not_null_fields.clear()
        for Model in self.models.values():
            if Model._auto and not Model._abstract:
                for field_name, field in Model._fields.items():
                    if field_name == 'id':
                        self.not_null_fields.add(field)
                        continue
                    if field.column_type and field.store and field.required:
                        if (Model._table, field_name) in not_null_columns:
                            self.not_null_fields.add(field)
                        else:
                            _schema.warning("Missing not-null constraint on %s", field)