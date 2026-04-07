def test_hash_uniqueness(self):
        constraint_name = "exclusion_equal_room_hash"
        self.assertNotIn(constraint_name, self.get_constraints(Room._meta.db_table))
        constraint = ExclusionConstraint(
            name=constraint_name,
            index_type="hash",
            expressions=[(F("number"), RangeOperators.EQUAL)],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Room, constraint)
        self.assertIn(constraint_name, self.get_constraints(Room._meta.db_table))
        Room.objects.create(number=101)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Room.objects.create(number=101)
        Room.objects.create(number=102)
        # Drop the constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(Room, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(Room._meta.db_table))