def test_foreign_data_wrapper(self):
        cursor_execute(
            "CREATE EXTENSION IF NOT EXISTS file_fdw",
            "CREATE SERVER inspectdb_server FOREIGN DATA WRAPPER file_fdw",
            """
            CREATE FOREIGN TABLE inspectdb_iris_foreign_table (
                petal_length real,
                petal_width real,
                sepal_length real,
                sepal_width real
            ) SERVER inspectdb_server OPTIONS (
                program 'echo 1,2,3,4',
                format 'csv'
            )
            """,
        )
        self.addCleanup(
            cursor_execute,
            "DROP FOREIGN TABLE IF EXISTS inspectdb_iris_foreign_table",
            "DROP SERVER IF EXISTS inspectdb_server",
            "DROP EXTENSION IF EXISTS file_fdw",
        )
        out = StringIO()
        foreign_table_model = "class InspectdbIrisForeignTable(models.Model):"
        foreign_table_managed = "managed = False"
        call_command(
            "inspectdb",
            table_name_filter=inspectdb_tables_only,
            stdout=out,
        )
        output = out.getvalue()
        self.assertIn(foreign_table_model, output)
        self.assertIn(foreign_table_managed, output)