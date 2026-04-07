def test_time_field(self):
        field = models.TimeField()
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.TimeField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})

        field = models.TimeField(auto_now=True)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"auto_now": True})

        field = models.TimeField(auto_now_add=True)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"auto_now_add": True})