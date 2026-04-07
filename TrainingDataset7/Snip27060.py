def test_migrate_syncdb_installed_truncated_db_model(self):
        """
        Running migrate --run-syncdb doesn't try to create models with long
        truncated name if already exist.
        """
        with connection.cursor() as cursor:
            mock_existing_tables = connection.introspection.table_names(cursor)
        # Add truncated name for the VeryLongNameModel to the list of
        # existing table names.
        table_name = truncate_name(
            "long_db_table_that_should_be_truncated_before_checking",
            connection.ops.max_name_length(),
        )
        mock_existing_tables.append(table_name)
        stdout = io.StringIO()
        with (
            mock.patch.object(BaseDatabaseSchemaEditor, "execute") as execute,
            mock.patch.object(
                BaseDatabaseIntrospection,
                "table_names",
                return_value=mock_existing_tables,
            ),
        ):
            call_command(
                "migrate", "unmigrated_app_syncdb", run_syncdb=True, stdout=stdout
            )
            create_table_calls = [
                str(call).upper()
                for call in execute.mock_calls
                if "CREATE TABLE" in str(call)
            ]
            self.assertEqual(len(create_table_calls), 2)
            self.assertGreater(len(execute.mock_calls), 2)
            self.assertFalse(
                any([table_name.upper() in call for call in create_table_calls])
            )
            self.assertIn(
                "Synchronize unmigrated app: unmigrated_app_syncdb", stdout.getvalue()
            )