def test_alter_db_comment(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Add comment.
        old_field = Author._meta.get_field("name")
        new_field = CharField(max_length=255, db_comment="Custom comment")
        new_field.set_attributes_from_name("name")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "name"),
            "Custom comment",
        )
        # Alter comment.
        old_field = new_field
        new_field = CharField(max_length=255, db_comment="New custom comment")
        new_field.set_attributes_from_name("name")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertEqual(
            self.get_column_comment(Author._meta.db_table, "name"),
            "New custom comment",
        )
        # Remove comment.
        old_field = new_field
        new_field = CharField(max_length=255)
        new_field.set_attributes_from_name("name")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertIn(
            self.get_column_comment(Author._meta.db_table, "name"),
            [None, ""],
        )