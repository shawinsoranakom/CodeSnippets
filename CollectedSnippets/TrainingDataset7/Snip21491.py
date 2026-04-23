def test_deconstruct(self):
        value = Value("name")
        path, args, kwargs = value.deconstruct()
        self.assertEqual(path, "django.db.models.Value")
        self.assertEqual(args, (value.value,))
        self.assertEqual(kwargs, {})