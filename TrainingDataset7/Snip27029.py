def test_migrate_conflict_exit(self):
        """
        migrate exits if it detects a conflict.
        """
        msg = (
            "Conflicting migrations detected; multiple leaf nodes in the "
            "migration graph: (0002_conflicting_second, 0002_second in "
            "migrations).\n"
            "To fix them run 'python manage.py makemigrations --merge'"
        )
        with self.assertRaisesMessage(CommandError, msg):
            call_command("migrate", "migrations")