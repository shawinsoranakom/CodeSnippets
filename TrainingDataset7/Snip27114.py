def test_makemigrations_migrations_modules_path_not_exist(self):
        """
        makemigrations creates migrations when specifying a custom location
        for migration files using MIGRATION_MODULES if the custom path
        doesn't already exist.
        """

        class SillyModel(models.Model):
            silly_field = models.BooleanField(default=False)

            class Meta:
                app_label = "migrations"

        out = io.StringIO()
        migration_module = "migrations.test_migrations_path_doesnt_exist.foo.bar"
        with self.temporary_migration_module(module=migration_module) as migration_dir:
            call_command("makemigrations", "migrations", stdout=out)

            # Migrations file is actually created in the expected path.
            initial_file = os.path.join(migration_dir, "0001_initial.py")
            self.assertTrue(os.path.exists(initial_file))

        # Command output indicates the migration is created.
        self.assertIn(" + Create model SillyModel", out.getvalue())