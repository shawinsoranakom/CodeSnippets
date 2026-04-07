def test_expressions_with_params(self):
        constraint_name = "scene_left_equal"
        self.assertNotIn(constraint_name, self.get_constraints(Scene._meta.db_table))
        constraint = ExclusionConstraint(
            name=constraint_name,
            expressions=[(Left("scene", 4), RangeOperators.EQUAL)],
        )
        with connection.schema_editor() as editor:
            editor.add_constraint(Scene, constraint)
        self.assertIn(constraint_name, self.get_constraints(Scene._meta.db_table))