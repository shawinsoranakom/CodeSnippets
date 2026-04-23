def test_add_foreign_key_long_names(self):
        """
        Regression test for #23009.
        Only affects databases that supports foreign keys.
        """
        # Create the initial tables
        with connection.schema_editor() as editor:
            editor.create_model(AuthorWithEvenLongerName)
            editor.create_model(BookWithLongName)
        # Add a second FK, this would fail due to long ref name before the fix
        new_field = ForeignKey(
            AuthorWithEvenLongerName, CASCADE, related_name="something"
        )
        new_field.set_attributes_from_name(
            "author_other_really_long_named_i_mean_so_long_fk"
        )
        with connection.schema_editor() as editor:
            editor.add_field(BookWithLongName, new_field)