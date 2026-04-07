def test_add_field_remove_field(self):
        """
        Adding a field and removing it removes all deferred sql referring to
        it.
        """
        with connection.schema_editor() as editor:
            # Create a table with a unique constraint on the slug field.
            editor.create_model(Tag)
            # Remove the slug column.
            editor.remove_field(Tag, Tag._meta.get_field("slug"))
        self.assertEqual(editor.deferred_sql, [])