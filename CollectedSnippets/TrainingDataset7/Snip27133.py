def test_makemigrations_continues_number_sequence_after_squash(self):
        with self.temporary_migration_module(
            module="migrations.test_migrations_squashed"
        ):
            with captured_stdout() as out:
                call_command(
                    "makemigrations",
                    "migrations",
                    interactive=False,
                    empty=True,
                )
            out_value = out.getvalue()
            self.assertIn("0003_auto", out_value)