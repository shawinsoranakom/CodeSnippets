def test_run_sql_add_missing_semicolon_on_collect_sql(self):
        project_state = self.set_up_test_model("test_runsql")
        new_state = project_state.clone()
        tests = [
            "INSERT INTO test_runsql_pony (pink, weight) VALUES (1, 1);\n",
            "INSERT INTO test_runsql_pony (pink, weight) VALUES (1, 1)\n",
        ]
        for sql in tests:
            with self.subTest(sql=sql):
                operation = migrations.RunSQL(sql, migrations.RunPython.noop)
                with connection.schema_editor(collect_sql=True) as editor:
                    operation.database_forwards(
                        "test_runsql", editor, project_state, new_state
                    )
                    collected_sql = "\n".join(editor.collected_sql)
                    self.assertEqual(collected_sql.count(";"), 1)