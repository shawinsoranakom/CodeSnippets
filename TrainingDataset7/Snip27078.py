def test_makemigrations_empty_connections(self):
        empty_connections = ConnectionHandler({"default": {}})
        with mock.patch(
            "django.core.management.commands.makemigrations.connections",
            new=empty_connections,
        ):
            # with no apps
            out = io.StringIO()
            call_command("makemigrations", stdout=out)
            self.assertIn("No changes detected", out.getvalue())
            # with an app
            with self.temporary_migration_module() as migration_dir:
                call_command("makemigrations", "migrations", verbosity=0)
                init_file = os.path.join(migration_dir, "__init__.py")
                self.assertTrue(os.path.exists(init_file))