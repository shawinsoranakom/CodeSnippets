def test_query_other_database_using_stored_procedure(self):
        connection = connections["other"]
        with connection.cursor() as cursor:
            cursor.execute(connection.features.create_test_procedure_without_params_sql)

        try:
            self.run_setup("QueryOtherDatabaseStoredProcedureAppConfig")
        finally:
            with connection.schema_editor() as editor:
                editor.remove_procedure("test_procedure")