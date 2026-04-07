def test_alter(self):
        """
        Tests simple altering of fields
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Ensure the field is right to begin with
        columns = self.column_classes(Author)
        self.assertEqual(
            columns["name"][0],
            connection.features.introspected_field_types["CharField"],
        )
        self.assertEqual(
            bool(columns["name"][1][6]),
            bool(connection.features.interprets_empty_strings_as_nulls),
        )
        # Alter the name field to a TextField
        old_field = Author._meta.get_field("name")
        new_field = TextField(null=True)
        new_field.set_attributes_from_name("name")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        columns = self.column_classes(Author)
        self.assertEqual(columns["name"][0], "TextField")
        self.assertTrue(columns["name"][1][6])
        # Change nullability again
        new_field2 = TextField(null=False)
        new_field2.set_attributes_from_name("name")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, new_field, new_field2, strict=True)
        columns = self.column_classes(Author)
        self.assertEqual(columns["name"][0], "TextField")
        self.assertEqual(
            bool(columns["name"][1][6]),
            bool(connection.features.interprets_empty_strings_as_nulls),
        )