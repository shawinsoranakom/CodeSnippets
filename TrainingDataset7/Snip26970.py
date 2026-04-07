def test_two_create_models_with_initial_true(self):
        class Migration(migrations.Migration):
            initial = True
            operations = [
                migrations.CreateModel("Person", fields=[]),
                migrations.CreateModel("Animal", fields=[]),
            ]

        migration = Migration("0001_initial", "test_app")
        self.assertEqual(migration.suggest_name(), "initial")