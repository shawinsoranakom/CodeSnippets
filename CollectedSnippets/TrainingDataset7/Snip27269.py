def test_valid(self):
        """
        To support frozen environments, MigrationLoader loads .pyc migrations.
        """
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            # Compile .py files to .pyc files and delete .py files.
            compileall.compile_dir(migration_dir, force=True, quiet=1, legacy=True)
            for name in os.listdir(migration_dir):
                if name.endswith(".py"):
                    os.remove(os.path.join(migration_dir, name))
            loader = MigrationLoader(connection)
            self.assertIn(("migrations", "0001_initial"), loader.disk_migrations)