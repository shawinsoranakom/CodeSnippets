def test_check_constraint_range_lower_upper(self):
        constraint = CheckConstraint(
            condition=Q(ints__startswith__gte=0) & Q(ints__endswith__lte=99),
            name="ints_range_lower_upper",
        )
        msg = f"Constraint “{constraint.name}” is violated."
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(RangesModel, RangesModel(ints=(-1, 20)))
        with self.assertRaisesMessage(ValidationError, msg):
            constraint.validate(RangesModel, RangesModel(ints=(0, 100)))
        constraint.validate(RangesModel, RangesModel(ints=(0, 99)))