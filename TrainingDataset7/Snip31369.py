def test_rename_field_with_check_to_truncated_name(self):
        class AuthorWithLongColumn(Model):
            field_with_very_looooooong_name = PositiveIntegerField(null=True)

            class Meta:
                app_label = "schema"

        self.isolated_local_models = [AuthorWithLongColumn]
        with connection.schema_editor() as editor:
            editor.create_model(AuthorWithLongColumn)
        old_field = AuthorWithLongColumn._meta.get_field(
            "field_with_very_looooooong_name"
        )
        new_field = PositiveIntegerField(null=True)
        new_field.set_attributes_from_name("renamed_field_with_very_long_name")
        with connection.schema_editor() as editor:
            editor.alter_field(AuthorWithLongColumn, old_field, new_field, strict=True)

        new_field_name = truncate_name(
            new_field.column, connection.ops.max_name_length()
        )
        constraints = self.get_constraints(AuthorWithLongColumn._meta.db_table)
        check_constraints = [
            name
            for name, details in constraints.items()
            if details["columns"] == [new_field_name] and details["check"]
        ]
        self.assertEqual(len(check_constraints), 1)