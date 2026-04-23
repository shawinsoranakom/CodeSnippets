def test_invalid_deferrable(self):
        msg = "ExclusionConstraint.deferrable must be a Deferrable instance."
        with self.assertRaisesMessage(ValueError, msg):
            ExclusionConstraint(
                name="exclude_invalid_deferrable",
                expressions=[(F("datespan"), RangeOperators.OVERLAPS)],
                deferrable="invalid",
            )