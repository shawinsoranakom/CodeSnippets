def test_alter_model_managers_emptying(self):
        """
        The managers on a model are set.
        """
        project_state = self.set_up_test_model("test_almomae", manager_model=True)
        # Test the state alteration
        operation = migrations.AlterModelManagers("Food", managers=[])
        self.assertEqual(operation.describe(), "Change managers on Food")
        self.assertIn(("test_almomae", "food"), project_state.models)
        managers = project_state.models["test_almomae", "food"].managers
        self.assertEqual(managers[0][0], "food_qs")
        self.assertIsInstance(managers[0][1], models.Manager)
        self.assertEqual(managers[1][0], "food_mgr")
        self.assertIsInstance(managers[1][1], FoodManager)
        self.assertEqual(managers[1][1].args, ("a", "b", 1, 2))
        self.assertEqual(managers[2][0], "food_mgr_kwargs")
        self.assertIsInstance(managers[2][1], FoodManager)
        self.assertEqual(managers[2][1].args, ("x", "y", 3, 4))

        new_state = project_state.clone()
        operation.state_forwards("test_almomae", new_state)
        managers = new_state.models["test_almomae", "food"].managers
        self.assertEqual(managers, [])