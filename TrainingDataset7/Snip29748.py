def test_range_equal_cast(self):
        constraint_name = "exclusion_equal_room_cast"
        self.assertNotIn(constraint_name, self.get_constraints(Room._meta.db_table))
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[(Cast("number", IntegerField()), RangeOperators.EQUAL)],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Room, constraint)
        self.assertIn(constraint_name, self.get_constraints(Room._meta.db_table))