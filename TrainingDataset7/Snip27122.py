def test_makemigrations_check_with_changes(self):
        """
        makemigrations --check should exit with a non-zero status when
        there are changes to an app requiring migrations.
        """
        out = io.StringIO()
        with self.temporary_migration_module() as tmpdir:
            with self.assertRaises(SystemExit) as cm:
                call_command(
                    "makemigrations",
                    "--check",
                    "migrations",
                    stdout=out,
                )
            self.assertEqual(os.listdir(tmpdir), ["__init__.py"])
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Migrations for 'migrations':", out.getvalue())