def test_load_module_file(self):
        with override_settings(
            MIGRATION_MODULES={"migrations": "migrations.faulty_migrations.file"}
        ):
            loader = MigrationLoader(connection)
            self.assertIn(
                "migrations",
                loader.unmigrated_apps,
                "App with migrations module file not in unmigrated apps.",
            )