def test_makemigrations_migrations_modules_nonexistent_toplevel_package(self):
        msg = (
            "Could not locate an appropriate location to create migrations "
            "package some.nonexistent.path. Make sure the toplevel package "
            "exists and can be imported."
        )
        with self.assertRaisesMessage(ValueError, msg):
            call_command("makemigrations", "migrations", empty=True, verbosity=0)