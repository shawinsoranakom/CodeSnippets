def test_choices_iterator(self):
        field = models.IntegerField(choices=((i, str(i)) for i in range(3)))
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.IntegerField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"choices": [(0, "0"), (1, "1"), (2, "2")]})