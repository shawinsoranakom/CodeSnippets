def test_filter_not_equals_other_field(self):
        """
        We can filter for objects, where a value is not equals the value
        of an other field.
        """
        self.assertEqual(
            Number.objects.filter(integer__gt=0).update(integer=F("integer") + 1), 2
        )
        self.assertQuerySetEqual(
            Number.objects.exclude(float=F("integer")),
            [(43, 42), (1338, 1337)],
            lambda n: (n.integer, round(n.float)),
            ordered=False,
        )