def test_load_import_error(self):
        with override_settings(
            MIGRATION_MODULES={"migrations": "import_error_package"}
        ):
            with self.assertRaises(ImportError):
                MigrationLoader(connection)