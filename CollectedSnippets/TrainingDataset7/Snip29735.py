def test_range_adjacent_initially_deferred(self):
        constraint_name = "ints_adjacent_deferred"
        self.assertNotIn(
            constraint_name, self.get_constraints(RangesModel._meta.db_table)
        )
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[("ints", RangeOperators.ADJACENT_TO)],
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
                cursor.execute("SET CONSTRAINTS %s IMMEDIATE" % quoted_name)
        # Remove adjacent range before the end of transaction.
        adjacent_range.delete()
        RangesModel.objects.create(ints=(10, 19))
        RangesModel.objects.create(ints=(51, 60))