def test_many_operations_suffix(self):
        class Migration(migrations.Migration):
            operations = [
                migrations.CreateModel("Person1", fields=[]),
                migrations.CreateModel("Person2", fields=[]),
                migrations.CreateModel("Person3", fields=[]),
                migrations.DeleteModel("Person4"),
                migrations.DeleteModel("Person5"),
            ]

        migration = Migration("some_migration", "test_app")
        self.assertEqual(
            migration.suggest_name(),
            "person1_person2_person3_delete_person4_and_more",
        )