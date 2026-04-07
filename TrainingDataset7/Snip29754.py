def test_non_equal_hash_index_not_supported(self):
        constraint_name = "none_equal_hash_index_not_supported"
        msg = (
            "Exclusion constraints using Hash indexes only support the EQUAL operator."
        )
        with self.assertRaisesMessage(ValueError, msg):
            ExclusionConstraint(
                name=constraint_name,
                expressions=[("int1", RangeOperators.NOT_EQUAL)],
                index_type="hash",
            )