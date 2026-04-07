def test_subclass_deconstruct(self):
        field = ArrayField(models.IntegerField())
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.fields.ArrayField")

        field = ArrayFieldSubclass()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "postgres_tests.models.ArrayFieldSubclass")