def test_positive_small_integer_field(self):
        field = models.PositiveSmallIntegerField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.PositiveSmallIntegerField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})