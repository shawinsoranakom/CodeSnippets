def test_abstract_name(self):
        constraints = get_constraints(ChildModel._meta.db_table)
        self.assertIn("constraints_childmodel_adult", constraints)