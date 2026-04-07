def test_repr_with_nulls_distinct(self):
        constraint = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="nulls_distinct_fields",
            nulls_distinct=False,
        )
        self.assertEqual(
            repr(constraint),
            "<UniqueConstraint: fields=('foo', 'bar') name='nulls_distinct_fields' "
            "nulls_distinct=False>",
        )