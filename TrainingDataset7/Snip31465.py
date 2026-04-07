def test_remove_constraints_capital_letters(self):
        """
        #23065 - Constraint names must be quoted if they contain capital
        letters.
        """

        def get_field(*args, field_class=BigIntegerField, **kwargs):
            kwargs["db_column"] = "CamelCase"
            field = field_class(*args, **kwargs)
            field.set_attributes_from_name("CamelCase")
            return field

        model = Author
        field = get_field()
        table = model._meta.db_table
        column = field.column
        identifier_converter = connection.introspection.identifier_converter

        with connection.schema_editor() as editor:
            editor.create_model(model)
            editor.add_field(model, field)

            constraint_name = "CamelCaseIndex"
            expected_constraint_name = identifier_converter(constraint_name)
            editor.execute(
                editor.sql_create_index
                % {
                    "table": editor.quote_name(table),
                    "name": editor.quote_name(constraint_name),
                    "using": "",
                    "columns": editor.quote_name(column),
                    "extra": "",
                    "condition": "",
                    "include": "",
                }
            )
            self.assertIn(
                expected_constraint_name, self.get_constraints(model._meta.db_table)
            )
            editor.alter_field(model, get_field(db_index=True), field, strict=True)
            self.assertNotIn(
                expected_constraint_name, self.get_constraints(model._meta.db_table)
            )

            constraint_name = "CamelCaseUniqConstraint"
            expected_constraint_name = identifier_converter(constraint_name)
            editor.execute(editor._create_unique_sql(model, [field], constraint_name))
            self.assertIn(
                expected_constraint_name, self.get_constraints(model._meta.db_table)
            )
            editor.alter_field(model, get_field(unique=True), field, strict=True)
            self.assertNotIn(
                expected_constraint_name, self.get_constraints(model._meta.db_table)
            )

            if editor.sql_create_fk and connection.features.can_introspect_foreign_keys:
                constraint_name = "CamelCaseFKConstraint"
                expected_constraint_name = identifier_converter(constraint_name)
                editor.execute(
                    editor.sql_create_fk
                    % {
                        "table": editor.quote_name(table),
                        "name": editor.quote_name(constraint_name),
                        "column": editor.quote_name(column),
                        "to_table": editor.quote_name(table),
                        "to_column": editor.quote_name(model._meta.auto_field.column),
                        "deferrable": connection.ops.deferrable_sql(),
                        "on_delete_db": "",
                    }
                )
                self.assertIn(
                    expected_constraint_name, self.get_constraints(model._meta.db_table)
                )
                editor.alter_field(
                    model,
                    get_field(Author, CASCADE, field_class=ForeignKey),
                    field,
                    strict=True,
                )
                self.assertNotIn(
                    expected_constraint_name, self.get_constraints(model._meta.db_table)
                )