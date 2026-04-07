def test_none_name_with_initial_true(self):
        class Migration(migrations.Migration):
            initial = True
            operations = [migrations.RunSQL("SELECT 1 FROM person;")]

        migration = Migration("0001_initial", "test_app")
        self.assertEqual(migration.suggest_name(), "initial")