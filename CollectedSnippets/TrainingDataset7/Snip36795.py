def test_func_unique_constraint_ignored(self):
        m = UniqueFuncConstraintModel()
        self.assertEqual(
            m._get_unique_checks(),
            ([(UniqueFuncConstraintModel, ("id",))], []),
        )