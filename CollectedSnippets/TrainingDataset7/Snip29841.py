def test_partial_gin_index_with_tablespace(self):
        with register_lookup(CharField, Length):
            index_name = "char_field_gin_partial_idx"
            index = GinIndex(
                fields=["field"],
                name=index_name,
                condition=Q(field__length=40),
                db_tablespace="pg_default",
            )
            with connection.schema_editor() as editor:
                editor.add_index(CharFieldModel, index)
                self.assertIn(
                    'TABLESPACE "pg_default" ',
                    str(index.create_sql(CharFieldModel, editor)),
                )
            constraints = self.get_constraints(CharFieldModel._meta.db_table)
            self.assertEqual(constraints[index_name]["type"], "gin")
            with connection.schema_editor() as editor:
                editor.remove_index(CharFieldModel, index)
            self.assertNotIn(
                index_name, self.get_constraints(CharFieldModel._meta.db_table)
            )