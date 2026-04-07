def test_deconstruct(self):
        f = F("name")
        path, args, kwargs = f.deconstruct()
        self.assertEqual(path, "django.db.models.F")
        self.assertEqual(args, (f.name,))
        self.assertEqual(kwargs, {})