def test_repr_with_include(self):
        constraint = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="include_fields",
            include=["baz_1", "baz_2"],
        )
        self.assertEqual(
            repr(constraint),
            "<UniqueConstraint: fields=('foo', 'bar') name='include_fields' "
            "include=('baz_1', 'baz_2')>",
        )