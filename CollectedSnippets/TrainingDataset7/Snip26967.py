def test_single_operation_long_name(self):
        class Migration(migrations.Migration):
            operations = [migrations.CreateModel("A" * 53, fields=[])]

        migration = Migration("some_migration", "test_app")
        self.assertEqual(migration.suggest_name(), "a" * 53)