def test_add_field_both_defaults_preserves_db_default(self):
        class Author(Model):
            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Author)

        field = IntegerField(default=1985, db_default=1988)
        field.set_attributes_from_name("birth_year")
        field.model = Author
        with connection.schema_editor() as editor:
            editor.add_field(Author, field)
        columns = self.column_classes(Author)
        self.assertEqual(columns["birth_year"][1].default, "1988")