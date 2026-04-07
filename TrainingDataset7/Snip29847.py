def test_brin_index(self):
        index_name = "char_field_model_field_brin"
        index = BrinIndex(fields=["field"], name=index_name, pages_per_range=4)
        with connection.schema_editor() as editor:
            editor.add_index(CharFieldModel, index)
        constraints = self.get_constraints(CharFieldModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], BrinIndex.suffix)
        self.assertEqual(constraints[index_name]["options"], ["pages_per_range=4"])
        with connection.schema_editor() as editor:
            editor.remove_index(CharFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(CharFieldModel._meta.db_table)
        )