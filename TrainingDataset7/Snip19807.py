def test_repr_with_deferrable(self):
        constraint = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="unique_fields",
            deferrable=models.Deferrable.IMMEDIATE,
        )
        self.assertEqual(
            repr(constraint),
            "<UniqueConstraint: fields=('foo', 'bar') name='unique_fields' "
            "deferrable=Deferrable.IMMEDIATE>",
        )