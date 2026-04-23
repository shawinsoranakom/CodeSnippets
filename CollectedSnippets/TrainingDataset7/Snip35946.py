def test_check_migrations(self):
        requires_migrations_checks = dance.Command.requires_migrations_checks
        self.assertIs(requires_migrations_checks, False)
        try:
            with mock.patch.object(BaseCommand, "check_migrations") as check_migrations:
                management.call_command("dance", verbosity=0)
                self.assertFalse(check_migrations.called)
                dance.Command.requires_migrations_checks = True
                management.call_command("dance", verbosity=0)
                self.assertTrue(check_migrations.called)
        finally:
            dance.Command.requires_migrations_checks = requires_migrations_checks