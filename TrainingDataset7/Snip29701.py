def test_check_constraint_range_contains(self):
        constraint = CheckConstraint(
            condition=Q(ints__contains=(1, 5)),
            name="ints_contains",
        )
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(RangesModel, RangesModel(ints=(6, 10)))