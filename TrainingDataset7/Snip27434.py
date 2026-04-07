def test_run_sql_noop(self):
        """
        #24098 - Tests no-op RunSQL operations.
        """
        operation = migrations.RunSQL(migrations.RunSQL.noop, migrations.RunSQL.noop)
        with connection.schema_editor() as editor:
            operation.database_forwards("test_runsql", editor, None, None)
            operation.database_backwards("test_runsql", editor, None, None)