def test_spgist_parameters(self):
        index_name = "text_field_model_spgist_fillfactor"
        index = SpGistIndex(fields=["field"], name=index_name, fillfactor=80)
        with connection.schema_editor() as editor:
            editor.add_index(TextFieldModel, index)
        constraints = self.get_constraints(TextFieldModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], SpGistIndex.suffix)
        self.assertEqual(constraints[index_name]["options"], ["fillfactor=80"])
        with connection.schema_editor() as editor:
            editor.remove_index(TextFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(TextFieldModel._meta.db_table)
        )