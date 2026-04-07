def test_range_adjacent_opclass_deferrable(self):
        constraint_name = "ints_adjacent_opclass_deferrable"
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[
                (OpClass("ints", name="range_ops"), RangeOperators.ADJACENT_TO),
            ],
            deferrable=Deferrable.DEFERRED,
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(RangesModel, constraint)
        self.assertIn(constraint_name, self.get_constraints(RangesModel._meta.db_table))