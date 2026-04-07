def test_makemigrations_auto_now_add_interactive_quit(self, mock_input):
        class Author(models.Model):
            publishing_date = models.DateField(auto_now_add=True)

            class Meta:
                app_label = "migrations"

        with self.temporary_migration_module(module="migrations.test_migrations"):
            with captured_stdout():
                with self.assertRaises(SystemExit):
                    call_command("makemigrations", "migrations", interactive=True)