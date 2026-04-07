def test_none_name(self):
        class Migration(migrations.Migration):
            operations = [migrations.RunSQL("SELECT 1 FROM person;")]

        migration = Migration("0001_initial", "test_app")
        suggest_name = migration.suggest_name()
        self.assertIs(suggest_name.startswith("auto_"), True)