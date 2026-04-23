def test_gist_parameters(self):
        index_name = "integer_array_gist_buffering"
        index = GistIndex(
            fields=["field"], name=index_name, buffering=True, fillfactor=80
        )
        with connection.schema_editor() as editor:
            editor.add_index(CharFieldModel, index)
        constraints = self.get_constraints(CharFieldModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], GistIndex.suffix)
        self.assertEqual(
            constraints[index_name]["options"], ["buffering=on", "fillfactor=80"]
        )
        with connection.schema_editor() as editor:
            editor.remove_index(CharFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(CharFieldModel._meta.db_table)
        )