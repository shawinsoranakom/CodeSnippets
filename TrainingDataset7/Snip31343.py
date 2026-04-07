def test_alter_fk(self):
        """
        Tests altering of FKs
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        # Ensure the field is right to begin with
        columns = self.column_classes(Book)
        self.assertEqual(
            columns["author_id"][0],
            connection.features.introspected_field_types["BigIntegerField"],
        )
        self.assertForeignKeyExists(Book, "author_id", "schema_author")
        # Alter the FK
        old_field = Book._meta.get_field("author")
        new_field = ForeignKey(Author, CASCADE, editable=False)
        new_field.set_attributes_from_name("author")
        with connection.schema_editor() as editor:
            editor.alter_field(Book, old_field, new_field, strict=True)
        columns = self.column_classes(Book)
        self.assertEqual(
            columns["author_id"][0],
            connection.features.introspected_field_types["BigIntegerField"],
        )
        self.assertForeignKeyExists(Book, "author_id", "schema_author")