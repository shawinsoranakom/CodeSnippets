def test_makemigrations_conflict_exit(self):
        """
        makemigrations exits if it detects a conflict.
        """
        with self.temporary_migration_module(
            module="migrations.test_migrations_conflict"
        ):
            with self.assertRaises(CommandError) as context:
                call_command("makemigrations")
        self.assertEqual(
            str(context.exception),
            "Conflicting migrations detected; multiple leaf nodes in the "
            "migration graph: (0002_conflicting_second, 0002_second in "
            "migrations).\n"
            "To fix them run 'python manage.py makemigrations --merge'",
        )