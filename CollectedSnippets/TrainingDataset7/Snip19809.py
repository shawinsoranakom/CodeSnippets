def test_repr_with_opclasses(self):
        constraint = models.UniqueConstraint(
            fields=["foo", "bar"],
            name="opclasses_fields",
            opclasses=["text_pattern_ops", "varchar_pattern_ops"],
        )
        self.assertEqual(
            repr(constraint),
            "<UniqueConstraint: fields=('foo', 'bar') name='opclasses_fields' "
            "opclasses=['text_pattern_ops', 'varchar_pattern_ops']>",
        )