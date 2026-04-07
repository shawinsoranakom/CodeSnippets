def test_alter_charfield_to_null(self):
        """
        #24307 - Should skip an alter statement on databases with
        interprets_empty_strings_as_nulls when changing a CharField to null.
        """
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        # Change the CharField to null
        old_field = Author._meta.get_field("name")
        new_field = copy(old_field)
        new_field.null = True
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)