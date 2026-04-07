def test_gin_fastupdate(self):
        index_name = "integer_array_gin_fastupdate"
        index = GinIndex(fields=["field"], name=index_name, fastupdate=False)
        with connection.schema_editor() as editor:
            editor.add_index(IntegerArrayModel, index)
        constraints = self.get_constraints(IntegerArrayModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], "gin")
        self.assertEqual(constraints[index_name]["options"], ["fastupdate=off"])
        with connection.schema_editor() as editor:
            editor.remove_index(IntegerArrayModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(IntegerArrayModel._meta.db_table)
        )