def test_deconstruct(self):
        jsonnull = JSONNull()
        path, args, kwargs = jsonnull.deconstruct()
        self.assertEqual(path, "django.db.models.JSONNull")
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})