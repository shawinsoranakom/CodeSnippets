def test_alter_textual_field_not_null_to_null(self):
        """
        Nullability for textual fields is preserved on databases that
        interpret empty strings as NULLs.
        """
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        columns = self.column_classes(Author)
        # Field is nullable.
        self.assertTrue(columns["uuid"][1][6])
        # Change to NOT NULL.
        old_field = Author._meta.get_field("uuid")
        new_field = SlugField(null=False, blank=True)
        new_field.set_attributes_from_name("uuid")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        columns = self.column_classes(Author)
        # Nullability is preserved.
        self.assertTrue(columns["uuid"][1][6])