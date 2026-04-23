def test_single_operation(self):
        class Migration(migrations.Migration):
            operations = [migrations.CreateModel("Person", fields=[])]

        migration = Migration("0001_initial", "test_app")
        self.assertEqual(migration.suggest_name(), "person")

        class Migration(migrations.Migration):
            operations = [migrations.DeleteModel("Person")]

        migration = Migration("0002_initial", "test_app")
        self.assertEqual(migration.suggest_name(), "delete_person")