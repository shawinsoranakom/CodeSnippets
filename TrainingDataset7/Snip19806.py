def test_repr_with_condition(self):
        constraint = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="unique_fields",
            condition=models.Q(foo=models.F("bar")),
        )
        self.assertEqual(
            repr(constraint),
            "<UniqueConstraint: fields=('foo', 'bar') name='unique_fields' "
            "condition=(AND: ('foo', F(bar)))>",
        )