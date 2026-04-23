def test_invalid_condition(self):
        msg = "ExclusionConstraint.condition must be a Q instance."
        with self.assertRaisesMessage(ValueError, msg):
            ExclusionConstraint(
                index_type="GIST",
                name="exclude_invalid_condition",
                expressions=[(F("datespan"), RangeOperators.OVERLAPS)],
                condition=F("invalid"),
            )