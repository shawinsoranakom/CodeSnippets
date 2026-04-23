def test_eq_with_condition(self):
        self.assertEqual(
            models.UniqueConstraint(
                fields=["foo", "bar"],
                name="unique",
                condition=models.Q(foo=models.F("bar")),
            ),
            models.UniqueConstraint(
                fields=["foo", "bar"],
                name="unique",
                condition=models.Q(foo=models.F("bar")),
            ),
        )
        self.assertNotEqual(
            models.UniqueConstraint(
                fields=["foo", "bar"],
                name="unique",
                condition=models.Q(foo=models.F("bar")),
            ),
            models.UniqueConstraint(
                fields=["foo", "bar"],
                name="unique",
                condition=models.Q(foo=models.F("baz")),
            ),
        )