def test_add_text_field_with_db_default(self):
        class Author(Model):
            description = TextField(db_default="(missing)")

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Author)
        columns = self.column_classes(Author)
        self.assertIn("(missing)", columns["description"][1].default)