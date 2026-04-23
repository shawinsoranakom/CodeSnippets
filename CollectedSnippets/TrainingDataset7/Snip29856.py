def test_hash_index(self):
        # Ensure the table is there and doesn't have an index.
        self.assertNotIn("field", self.get_constraints(CharFieldModel._meta.db_table))
        # Add the index.
        index_name = "char_field_model_field_hash"
        index = HashIndex(fields=["field"], name=index_name)
        with connection.schema_editor() as editor:
            editor.add_index(CharFieldModel, index)
        constraints = self.get_constraints(CharFieldModel._meta.db_table)
        # The index was added.
        self.assertEqual(constraints[index_name]["type"], HashIndex.suffix)
        # Drop the index.
        with connection.schema_editor() as editor:
            editor.remove_index(CharFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(CharFieldModel._meta.db_table)
        )