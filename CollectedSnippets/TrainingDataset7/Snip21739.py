def test_choices_callable(self):
        def get_choices():
            return [(i, str(i)) for i in range(3)]

        field = models.IntegerField(choices=get_choices)
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.IntegerField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"choices": get_choices})