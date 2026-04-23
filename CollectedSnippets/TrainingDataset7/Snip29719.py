def test_eq(self):
        constraint_1 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                (F("datespan"), RangeOperators.OVERLAPS),
                (F("room"), RangeOperators.EQUAL),
            ],
            condition=Q(cancelled=False),
        )
        constraint_2 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
        )
        constraint_3 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[("datespan", RangeOperators.OVERLAPS)],
            condition=Q(cancelled=False),
        )
        constraint_4 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
            deferrable=Deferrable.DEFERRED,
        )
        constraint_5 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
            deferrable=Deferrable.IMMEDIATE,
        )
        constraint_6 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
            deferrable=Deferrable.IMMEDIATE,
            include=["cancelled"],
        )
        constraint_7 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
            include=["cancelled"],
        )
        constraint_8 = ExclusionConstraint(
            index_type="gist",
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
            include=["cancelled"],
        )
        constraint_9 = ExclusionConstraint(
            index_type="GIST",
            name="exclude_overlapping",
            expressions=[
                ("datespan", RangeOperators.OVERLAPS),
                ("room", RangeOperators.EQUAL),
            ],
            include=["cancelled"],
        )
        constraint_10 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                (F("datespan"), RangeOperators.OVERLAPS),
                (F("room"), RangeOperators.EQUAL),
            ],
            condition=Q(cancelled=False),
            violation_error_message="custom error",
        )
        constraint_11 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                (F("datespan"), RangeOperators.OVERLAPS),
                (F("room"), RangeOperators.EQUAL),
            ],
            condition=Q(cancelled=False),
            violation_error_message="other custom error",
        )
        constraint_12 = ExclusionConstraint(
            name="exclude_overlapping",
            expressions=[
                (F("datespan"), RangeOperators.OVERLAPS),
                (F("room"), RangeOperators.EQUAL),
            ],
            condition=Q(cancelled=False),
            violation_error_code="custom_code",
            violation_error_message="other custom error",
        )
        constraint_13 = ExclusionConstraint(
            name="exclude_equal_hash",
            index_type="hash",
            expressions=[(F("room"), RangeOperators.EQUAL)],
            violation_error_code="room_must_be_unique",
        )
        self.assertEqual(constraint_1, constraint_1)
        self.assertEqual(constraint_1, mock.ANY)
        self.assertNotEqual(constraint_1, constraint_2)
        self.assertNotEqual(constraint_1, constraint_3)
        self.assertNotEqual(constraint_1, constraint_4)
        self.assertNotEqual(constraint_1, constraint_10)
        self.assertNotEqual(constraint_2, constraint_3)
        self.assertNotEqual(constraint_2, constraint_4)
        self.assertNotEqual(constraint_2, constraint_7)
        self.assertEqual(constraint_7, constraint_8)
        self.assertEqual(constraint_7, constraint_9)
        self.assertNotEqual(constraint_4, constraint_5)
        self.assertNotEqual(constraint_5, constraint_6)
        self.assertNotEqual(constraint_1, object())
        self.assertNotEqual(constraint_10, constraint_11)
        self.assertNotEqual(constraint_11, constraint_12)
        self.assertNotEqual(constraint_12, constraint_13)
        self.assertEqual(constraint_10, constraint_10)
        self.assertEqual(constraint_12, constraint_12)
        self.assertEqual(constraint_13, constraint_13)