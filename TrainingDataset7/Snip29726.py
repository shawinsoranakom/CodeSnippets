def test_range_overlaps_custom(self):
        class TsTzRange(Func):
            function = "TSTZRANGE"
            output_field = DateTimeRangeField()

        constraint = ExclusionConstraint(
            name="exclude_overlapping_reservations_custom_opclass",
            expressions=[
                (
                    OpClass(TsTzRange("start", "end", RangeBoundary()), "range_ops"),
                    RangeOperators.OVERLAPS,
                ),
                (OpClass("room", "gist_int8_ops"), RangeOperators.EQUAL),
            ],
            condition=Q(cancelled=False),
        )
        self._test_range_overlaps(constraint)