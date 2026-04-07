def test_migrate_not_reflected_changes(self):
        class NewModel1(models.Model):
            class Meta:
                app_label = "migrated_app"

        class NewModel2(models.Model):
            class Meta:
                app_label = "migrated_unapplied_app"

        out = io.StringIO()
        try:
            call_command("migrate", verbosity=0)
            call_command("migrate", stdout=out, no_color=True)
            self.assertEqual(
                "operations to perform:\n"
                "  apply all migrations: migrated_app, migrated_unapplied_app\n"
                "running migrations:\n"
                "  no migrations to apply.\n"
                "  your models in app(s): 'migrated_app', "
                "'migrated_unapplied_app' have changes that are not yet "
                "reflected in a migration, and so won't be applied.\n"
                "  run 'manage.py makemigrations' to make new migrations, and "
                "then re-run 'manage.py migrate' to apply them.\n",
                out.getvalue().lower(),
            )
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrated_app", "zero", verbosity=0)
            call_command("migrate", "migrated_unapplied_app", "zero", verbosity=0)