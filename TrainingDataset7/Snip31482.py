def test_alter_field_type_preserve_comment(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)

        comment = "This is the name."
        old_field = Author._meta.get_field("name")
        new_field = CharField(max_length=255, db_comment=comment)
        new_field.set_attributes_from_name("name")
        new_field.model = Author
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "name"),
            comment,
        )
        # Changing a field type should preserve the comment.
        old_field = new_field
        new_field = CharField(max_length=511, db_comment=comment)
        new_field.set_attributes_from_name("name")
        new_field.model = Author
        with connection.schema_editor() as editor:
            editor.alter_field(Author, new_field, old_field, strict=True)
        # Comment is preserved.
        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "name"),
            comment,
        )