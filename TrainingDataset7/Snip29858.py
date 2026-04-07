def test_spgist_index(self):
        # Ensure the table is there and doesn't have an index.
        self.assertNotIn("field", self.get_constraints(TextFieldModel._meta.db_table))
        # Add the index.
        index_name = "text_field_model_field_spgist"
        index = SpGistIndex(fields=["field"], name=index_name)
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
        constraints = self.get_constraints(TextFieldModel._meta.db_table)
        # The index was added.
        self.assertEqual(constraints[index_name]["type"], SpGistIndex.suffix)
        # Drop the index.
        with connection.schema_editor() as editor:
            editor.remove_index(TextFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(TextFieldModel._meta.db_table)
        )