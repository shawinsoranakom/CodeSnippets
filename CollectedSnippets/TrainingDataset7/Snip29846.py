def test_bloom_parameters(self):
        index_name = "char_field_model_field_bloom_params"
        index = BloomIndex(fields=["field"], name=index_name, length=512, columns=[3])
        with connection.schema_editor() as editor:
            editor.add_index(CharFieldModel, index)
        constraints = self.get_constraints(CharFieldModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], BloomIndex.suffix)
        self.assertEqual(constraints[index_name]["options"], ["length=512", "col1=3"])
        with connection.schema_editor() as editor:
            editor.remove_index(CharFieldModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(CharFieldModel._meta.db_table)
        )