def test_invalid_include_type(self):
        msg = "ExclusionConstraint.include must be a list or tuple."
        with self.assertRaisesMessage(ValueError, msg):
            ExclusionConstraint(
                name="exclude_invalid_include",
                expressions=[(F("datespan"), RangeOperators.OVERLAPS)],
                include="invalid",
            )