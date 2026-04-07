def test_choices_iterable(self):
        # Pass an iterable (but not an iterator) to choices.
        field = models.IntegerField(choices="012345")
        name, path, args, kwargs = field.deconstruct()
        self.assertEqual(path, "django.db.models.IntegerField")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"choices": normalize_choices("012345")})