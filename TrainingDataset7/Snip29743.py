def test_range_adjacent_opclass(self):
        constraint_name = "ints_adjacent_opclass"
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[
                (OpClass("ints", name="range_ops"), RangeOperators.ADJACENT_TO),
            ],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(RangesModel, constraint)
        constraints = self.get_constraints(RangesModel._meta.db_table)
        self.assertIn(constraint_name, constraints)
        with editor.connection.cursor() as cursor:
            cursor.execute(SchemaTests.get_opclass_query, [constraint_name])
            self.assertEqual(
                cursor.fetchall(),
                [("range_ops", constraint_name)],
            )
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