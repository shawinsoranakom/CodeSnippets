def test_two_create_models(self):
        class Migration(migrations.Migration):
            operations = [
                migrations.CreateModel("Person", fields=[]),
                migrations.CreateModel("Animal", fields=[]),
            ]

        migration = Migration("0001_initial", "test_app")
        self.assertEqual(migration.suggest_name(), "person_animal")