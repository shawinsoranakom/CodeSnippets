def test_remove_indexed_field(self):
        with connection.schema_editor() as editor:
            editor.create_model(AuthorCharFieldWithIndex)
        with connection.schema_editor() as editor:
            editor.remove_field(
                AuthorCharFieldWithIndex,
                AuthorCharFieldWithIndex._meta.get_field("char_field"),
            )
        columns = self.column_classes(AuthorCharFieldWithIndex)
        self.assertNotIn("char_field", columns)