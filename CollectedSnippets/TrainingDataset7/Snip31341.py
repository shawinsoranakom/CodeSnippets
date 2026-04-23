def test_alter_textfield_to_null(self):
        """
        #24307 - Should skip an alter statement on databases with
        interprets_empty_strings_as_nulls when changing a TextField to null.
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Note)
        # Change the TextField to null
        old_field = Note._meta.get_field("info")
        new_field = copy(old_field)
        new_field.null = True
        with connection.schema_editor() as editor:
            editor.alter_field(Note, old_field, new_field, strict=True)