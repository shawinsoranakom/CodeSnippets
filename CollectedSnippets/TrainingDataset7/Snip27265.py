def test_ignore_files(self):
        """Files prefixed with underscore, tilde, or dot aren't loaded."""
        loader = MigrationLoader(connection)
        loader.load_disk()
        migrations = [
            name for app, name in loader.disk_migrations if app == "migrations"
        ]
        self.assertEqual(migrations, ["0001_initial"])