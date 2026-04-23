def cleanup_test_tables(self):
        table_names = (
            frozenset(connection.introspection.table_names())
            - self._initial_table_names
        )
        with connection.schema_editor() as editor:
            with connection.constraint_checks_disabled():
                for table_name in table_names:
                    editor.execute(
                        editor.sql_delete_table
                        % {
                            "table": editor.quote_name(table_name),
                        }
                    )