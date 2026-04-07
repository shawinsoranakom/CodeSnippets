def test_fill_with_value_from_same_object(self):
        """
        We can fill a value in all objects with an other value of the
        same object.
        """
        self.assertQuerySetEqual(
            Number.objects.all(),
            [(-1, -1), (42, 42), (1337, 1337)],
            lambda n: (n.integer, round(n.float)),
            ordered=False,
        )