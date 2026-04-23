def test_range_adjacent_initially_deferred_with_condition(self):
        constraint_name = "ints_adjacent_deferred_with_condition"
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[("ints", RangeOperators.ADJACENT_TO)],
            condition=Q(ints__lt=(100, 200)),
            deferrable=Deferrable.DEFERRED,
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(RangesModel, constraint)
        self.assertIn(constraint_name, self.get_constraints(RangesModel._meta.db_table))
        RangesModel.objects.create(ints=(20, 50))
        adjacent_range = RangesModel.objects.create(ints=(10, 20))
        # Constraint behavior can be changed with SET CONSTRAINTS.
        with self.assertRaises(IntegrityError):
            with transaction.atomic(), connection.cursor() as cursor:
                quoted_name = connection.ops.quote_name(constraint_name)
                cursor.execute(f"SET CONSTRAINTS {quoted_name} IMMEDIATE")
        # Remove adjacent range before the end of transaction.
        adjacent_range.delete()
        RangesModel.objects.create(ints=(10, 19))
        RangesModel.objects.create(ints=(51, 60))
        # Add adjacent range that doesn't match the condition.
        RangesModel.objects.create(ints=(200, 500))
        adjacent_range = RangesModel.objects.create(ints=(100, 200))
        # Constraint behavior can be changed with SET CONSTRAINTS.
        with transaction.atomic(), connection.cursor() as cursor:
            quoted_name = connection.ops.quote_name(constraint_name)
            cursor.execute(f"SET CONSTRAINTS {quoted_name} IMMEDIATE")