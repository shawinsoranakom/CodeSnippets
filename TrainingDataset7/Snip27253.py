def test_load_empty_dir(self):
        with override_settings(
            MIGRATION_MODULES={"migrations": "migrations.faulty_migrations.namespace"}
        ):
            loader = MigrationLoader(connection)
            self.assertIn(
                "migrations",
                loader.unmigrated_apps,
                "App missing __init__.py in migrations module not in unmigrated apps.",
            )