def test_increment_value(self):
        """
        We can increment a value of all objects in a query set.
        """
        self.assertEqual(
            Number.objects.filter(integer__gt=0).update(integer=F("integer") + 1), 2
        )
        self.assertQuerySetEqual(
            Number.objects.all(),
            [(-1, -1), (43, 42), (1338, 1337)],
            lambda n: (n.integer, round(n.float)),
            ordered=False,
        )