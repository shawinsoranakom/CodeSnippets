def test_opclass(self):
        constraint = UniqueConstraint(
            name="test_opclass",
            fields=["scene"],
            opclasses=["varchar_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Scene, constraint)
        self.assertIn(constraint.name, self.get_constraints(Scene._meta.db_table))
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query, [constraint.name])
            self.assertEqual(
                cursor.fetchall(),
                [("varchar_pattern_ops", constraint.name)],
            )
        # Drop the constraint.
        with connection.schema_editor() as editor:
            editor.remove_constraint(Scene, constraint)
        self.assertNotIn(constraint.name, self.get_constraints(Scene._meta.db_table))