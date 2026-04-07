def test_no_operations_initial(self):
        class Migration(migrations.Migration):
            initial = True
            operations = []

        migration = Migration("some_migration", "test_app")
        self.assertEqual(migration.suggest_name(), "initial")