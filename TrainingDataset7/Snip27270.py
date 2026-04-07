def test_invalid(self):
        """
        MigrationLoader reraises ImportErrors caused by "bad magic number" pyc
        files with a more helpful message.
        """
        with self.temporary_migration_module(
            module="migrations.test_migrations_bad_pyc"
        ) as migration_dir:
            # The -tpl suffix is to avoid the pyc exclusion in MANIFEST.in.
            os.rename(
                os.path.join(migration_dir, "0001_initial.pyc-tpl"),
                os.path.join(migration_dir, "0001_initial.pyc"),
            )
            msg = (
                r"Couldn't import '\w+.migrations.0001_initial' as it appears "
                "to be a stale .pyc file."
            )
            with self.assertRaisesRegex(ImportError, msg):
                MigrationLoader(connection)