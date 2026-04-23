def test_covering_hash_index_not_supported(self):
        constraint_name = "covering_hash_index_not_supported"
        msg = "Covering exclusion constraints using Hash indexes are not supported."
        with self.assertRaisesMessage(ValueError, msg):
            ExclusionConstraint(
                name=constraint_name,
                expressions=[("int1", RangeOperators.EQUAL)],
                index_type="hash",
                include=["int2"],
            )