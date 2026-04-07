def test_partial_gin_index(self):
        with register_lookup(CharField, Length):
            index_name = "char_field_gin_partial_idx"
            index = GinIndex(
                fields=["field"], name=index_name, condition=Q(field__length=40)
            )
            with connection.schema_editor() as editor:
                editor.add_index(CharFieldModel, index)
            constraints = self.get_constraints(CharFieldModel._meta.db_table)
            self.assertEqual(constraints[index_name]["type"], "gin")
            with connection.schema_editor() as editor:
                editor.remove_index(CharFieldModel, index)
            self.assertNotIn(
                index_name, self.get_constraints(CharFieldModel._meta.db_table)
            )