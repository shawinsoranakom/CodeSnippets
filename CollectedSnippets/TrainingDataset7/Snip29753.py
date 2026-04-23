def test_composite_hash_index_not_supported(self):
        constraint_name = "composite_hash_index_not_supported"
        msg = "Composite exclusion constraints using Hash indexes are not supported."
        with self.assertRaisesMessage(ValueError, msg):
            ExclusionConstraint(
                name=constraint_name,
                expressions=[
                    ("int1", RangeOperators.EQUAL),
                    ("int2", RangeOperators.EQUAL),
                ],
                index_type="hash",
            )