def test_check_constraint_range_lower_with_nulls(self):
        constraint = CheckConstraint(
            condition=Q(ints__isnull=True) | Q(ints__startswith__gte=0),
            name="ints_optional_positive_range",
        )
        constraint.validate(RangesModel, RangesModel())
        constraint = CheckConstraint(
            condition=Q(ints__startswith__gte=0),
            name="ints_positive_range",
        )
        constraint.validate(RangesModel, RangesModel())