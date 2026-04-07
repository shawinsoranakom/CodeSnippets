def test_positive_integer_field(self):
        field = models.PositiveIntegerField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.PositiveIntegerField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})