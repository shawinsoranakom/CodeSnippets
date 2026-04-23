def test_database_default(self):
        constraint = ExclusionConstraint(
            name="ints_equal", expressions=[("ints", RangeOperators.EQUAL)]
        )
        RangesModel.objects.create()
        msg = "Constraint “ints_equal” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(RangesModel, RangesModel())