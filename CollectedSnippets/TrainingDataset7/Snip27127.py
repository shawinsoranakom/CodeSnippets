def test_makemigrations_inconsistent_history_db_failure(self):
        msg = (
            "Got an error checking a consistent migration history performed "
            "for database connection 'default': could not connect to server"
        )
        with mock.patch(
            "django.db.migrations.loader.MigrationLoader.check_consistent_history",
            side_effect=OperationalError("could not connect to server"),
        ):
            with self.temporary_migration_module():
                with self.assertWarns(RuntimeWarning) as cm:
                    call_command("makemigrations", verbosity=0)
                self.assertEqual(str(cm.warning), msg)