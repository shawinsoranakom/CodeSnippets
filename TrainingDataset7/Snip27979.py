def test_callable_choices(self):
        def get_choices():
            return {i: str(i) for i in range(3)}

        f = models.IntegerField(choices=get_choices)

        for i in get_choices():
            with self.subTest(i=i):
                self.assertEqual(i, f.clean(i, None))

        with self.assertRaises(ValidationError):
            f.clean("A", None)
        with self.assertRaises(ValidationError):
            f.clean("3", None)