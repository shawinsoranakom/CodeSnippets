def test_range_adjacent(self):
        constraint_name = "ints_adjacent"
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[("ints", RangeOperators.ADJACENT_TO)],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(RangesModel, constraint)
        self.assertIn(constraint_name, self.get_constraints(RangesModel._meta.db_table))
        RangesModel.objects.create(ints=(20, 50))
        with self.assertRaises(IntegrityError), transaction.atomic():
            RangesModel.objects.create(ints=(10, 20))
        RangesModel.objects.create(ints=(10, 19))
        RangesModel.objects.create(ints=(51, 60))
        # Drop the constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(RangesModel, constraint)
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )