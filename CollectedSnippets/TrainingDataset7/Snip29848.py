def test_brin_parameters(self):
        index_name = "char_field_brin_params"
        index = BrinIndex(fields=["field"], name=index_name, autosummarize=True)
        with connection.schema_editor() as editor:
            editor.add_index(CharFieldModel, index)
        constraints = self.get_constraints(CharFieldModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], BrinIndex.suffix)
        self.assertEqual(constraints[index_name]["options"], ["autosummarize=on"])
        with connection.schema_editor() as editor:
            editor.remove_index(CharFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(CharFieldModel._meta.db_table)
        )