def test_gin_parameters(self):
        index_name = "integer_array_gin_params"
        index = GinIndex(
            fields=["field"],
            name=index_name,
            fastupdate=True,
            gin_pending_list_limit=64,
            db_tablespace="pg_default",
        )
        with connection.schema_editor() as editor:
            editor.add_index(IntegerArrayModel, index)
            self.assertIn(
                ") WITH (gin_pending_list_limit = 64, fastupdate = on) TABLESPACE",
                str(index.create_sql(IntegerArrayModel, editor)),
            )
        constraints = self.get_constraints(IntegerArrayModel._meta.db_table)
        self.assertEqual(constraints[index_name]["type"], "gin")
        self.assertEqual(
            constraints[index_name]["options"],
            ["gin_pending_list_limit=64", "fastupdate=on"],
        )
        with connection.schema_editor() as editor:
            editor.remove_index(IntegerArrayModel, index)
        self.assertNotIn(
            index_name, self.get_constraints(IntegerArrayModel._meta.db_table)
        )