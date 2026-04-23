def test_add_field_use_effective_default(self):
        """
        #23987 - effective_default() should be used as the field default when
        adding a new field.
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Ensure there's no surname field
        columns = self.column_classes(Author)
        self.assertNotIn("surname", columns)
        # Create a row
        Author.objects.create(name="Anonymous1")
        # Add new CharField to ensure default will be used from
        # effective_default
        new_field = CharField(max_length=15, blank=True)
        new_field.set_attributes_from_name("surname")
        with connection.schema_editor() as editor:
            editor.add_field(Author, new_field)
        # Ensure field was added with the right default
        with connection.cursor() as cursor:
            cursor.execute("SELECT surname FROM schema_author;")
            item = cursor.fetchall()[0]
            self.assertEqual(
                item[0],
                None if connection.features.interprets_empty_strings_as_nulls else "",
            )