def test_custom_user(self):
        """
        Regression test for #22325 - references to a custom user model defined
        in the same app are not resolved correctly.
        """
        with isolate_lru_cache(global_apps.get_swappable_settings_name):
            executor = MigrationExecutor(connection)
            self.assertTableNotExists("migrations_author")
            self.assertTableNotExists("migrations_tribble")
            # Migrate forwards
            executor.migrate([("migrations", "0001_initial")])
            self.assertTableExists("migrations_author")
            self.assertTableExists("migrations_tribble")
            # The soft-application detection works.
            # Change table_names to not return auth_user during this as it
            # wouldn't be there in a normal run, and ensure migrations.Author
            # exists in the global app registry temporarily.
            with connection.cursor() as cursor:
                mock_existing_tables = [
                    x
                    for x in connection.introspection.table_names(cursor)
                    if x != "auth_user"
                ]
            migrations_apps = executor.loader.project_state(
                ("migrations", "0001_initial"),
            ).apps
            global_apps.get_app_config("migrations").models["author"] = (
                migrations_apps.get_model("migrations", "author")
            )
            try:
                with mock.patch.object(
                    BaseDatabaseIntrospection,
                    "table_names",
                    return_value=mock_existing_tables,
                ):
                    migration = executor.loader.get_migration("auth", "0001_initial")
                self.assertIs(executor.detect_soft_applied(None, migration)[0], True)
            finally:
                del global_apps.get_app_config("migrations").models["author"]
                # Migrate back to clean up the database.
                executor.loader.build_graph()
                executor.migrate([("migrations", None)])
                self.assertTableNotExists("migrations_author")
                self.assertTableNotExists("migrations_tribble")