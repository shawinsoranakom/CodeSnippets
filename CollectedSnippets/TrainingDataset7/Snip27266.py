def test_loading_namespace_package(self):
        """Migration directories without an __init__.py file are ignored."""
        loader = MigrationLoader(connection)
        loader.load_disk()
        migrations = [
            name for app, name in loader.disk_migrations if app == "migrations"
        ]
        self.assertEqual(migrations, [])