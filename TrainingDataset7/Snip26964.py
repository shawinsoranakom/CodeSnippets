def test_no_operations(self):
        class Migration(migrations.Migration):
            operations = []

        migration = Migration("some_migration", "test_app")
        self.assertIs(migration.suggest_name().startswith("auto_"), True)