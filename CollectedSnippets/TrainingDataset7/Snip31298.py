def test_add_field_temp_default(self):
        """
        Tests adding fields to models with a temporary default
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Ensure there's no age field
        columns = self.column_classes(Author)
        self.assertNotIn("age", columns)
        # Add some rows of data
        Author.objects.create(name="Andrew", height=30)
        Author.objects.create(name="Andrea")
        # Add a not-null field
        new_field = CharField(max_length=30, default="Godwin")
        new_field.set_attributes_from_name("surname")
        with connection.schema_editor() as editor:
            editor.add_field(Author, new_field)
        columns = self.column_classes(Author)
        self.assertEqual(
            columns["surname"][0],
            connection.features.introspected_field_types["CharField"],
        )
        self.assertEqual(
            columns["surname"][1][6],
            connection.features.interprets_empty_strings_as_nulls,
        )