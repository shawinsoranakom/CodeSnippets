def test_gin_index(self):
        # Ensure the table is there and doesn't have an index.
        self.assertNotIn(
            "field", self.get_constraints(IntegerArrayModel._meta.db_table)
        )
        # Add the index
        index_name = "integer_array_model_field_gin"
        index = GinIndex(fields=["field"], name=index_name)
        with connection.schema_editor() as editor:
            editor.add_index(IntegerArrayModel, index)
        constraints = self.get_constraints(IntegerArrayModel._meta.db_table)
        # Check gin index was added
        self.assertEqual(constraints[index_name]["type"], GinIndex.suffix)
        # Drop the index
        with connection.schema_editor() as editor:
            editor.remove_index(IntegerArrayModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(IntegerArrayModel._meta.db_table)
        )