def test_rename_keep_db_default(self):
        """Renaming a field shouldn't affect a database default."""

        class AuthorDbDefault(Model):
            birth_year = IntegerField(db_default=1985)

            class Meta:
                app_label = "schema"

        self.isolated_local_models = [AuthorDbDefault]
        with connection.schema_editor() as editor:
            editor.create_model(AuthorDbDefault)
        columns = self.column_classes(AuthorDbDefault)
        self.assertEqual(columns["birth_year"][1].default, "1985")

        old_field = AuthorDbDefault._meta.get_field("birth_year")
        new_field = IntegerField(db_default=1985)
        new_field.set_attributes_from_name("renamed_year")
        new_field.model = AuthorDbDefault
        with connection.schema_editor() as editor:
            editor.alter_field(AuthorDbDefault, old_field, new_field, strict=True)
        columns = self.column_classes(AuthorDbDefault)
        self.assertEqual(columns["renamed_year"][1].default, "1985")