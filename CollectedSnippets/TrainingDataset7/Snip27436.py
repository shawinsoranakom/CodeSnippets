def test_run_sql_backward_reverse_sql_required(self):
        operation = migrations.RunSQL(sql=migrations.RunSQL.noop)
        msg = "You cannot reverse this operation"
        with (
            connection.schema_editor() as editor,
            self.assertRaisesMessage(NotImplementedError, msg),
        ):
            operation.database_backwards("test_runsql", editor, None, None)