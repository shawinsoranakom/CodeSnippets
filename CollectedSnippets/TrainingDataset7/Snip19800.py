def test_eq_with_deferrable(self):
        constraint_1 = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="unique",
            deferrable=models.Deferrable.DEFERRED,
        )
        constraint_2 = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="unique",
            deferrable=models.Deferrable.IMMEDIATE,
        )
        self.assertEqual(constraint_1, constraint_1)
        self.assertNotEqual(constraint_1, constraint_2)