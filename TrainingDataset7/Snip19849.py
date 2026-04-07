def test_name(self):
        constraints = get_constraints(UniqueConstraintProduct._meta.db_table)
        expected_name = "name_color_uniq"
        self.assertIn(expected_name, constraints)