def test_operation_with_no_suggested_name(self):
        class Migration(migrations.Migration):
            operations = [
                migrations.CreateModel("Person", fields=[]),
                migrations.RunSQL("SELECT 1 FROM person;"),
            ]

        migration = Migration("some_migration", "test_app")
        self.assertIs(migration.suggest_name().startswith("auto_"), True)