def test_hash_parameters(self):
        index_name = "integer_array_hash_fillfactor"
        index = HashIndex(fields=["field"], name=index_name, fillfactor=80)
        with connection.schema_editor() as editor:
            editor.add_index(CharFieldModel, index)
        constraints = self.get_constraints(CharFieldModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], HashIndex.suffix)
        self.assertEqual(constraints[index_name]["options"], ["fillfactor=80"])
        with connection.schema_editor() as editor:
            editor.remove_index(CharFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(CharFieldModel._meta.db_table)
        )