def test_two_operations(self):
        class Migration(migrations.Migration):
            operations = [
                migrations.CreateModel("Person", fields=[]),
                migrations.DeleteModel("Animal"),
            ]

        migration = Migration("some_migration", "test_app")
        self.assertEqual(migration.suggest_name(), "person_delete_animal")