def test_operation_with_invalid_chars_in_suggested_name(self):
        class Migration(migrations.Migration):
            operations = [
                migrations.AddConstraint(
                    "Person",
                    models.UniqueConstraint(
                        fields=["name"], name="person.name-*~unique!"
                    ),
                ),
            ]

        migration = Migration("some_migration", "test_app")
        self.assertEqual(migration.suggest_name(), "person_person_name_unique_")