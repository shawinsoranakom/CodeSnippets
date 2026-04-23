def test_alter_model_managers(self):
        """
        The managers on a model are set.
        """
        project_state = self.set_up_test_model("test_almoma")
        # Test the state alteration
        operation = migrations.AlterModelManagers(
            "Pony",
            managers=[
                ("food_qs", FoodQuerySet.as_manager()),
                ("food_mgr", FoodManager("a", "b")),
                ("food_mgr_kwargs", FoodManager("x", "y", 3, 4)),
            ],
        )
        self.assertEqual(operation.describe(), "Change managers on Pony")
        self.assertEqual(operation.formatted_description(), "~ Change managers on Pony")
        self.assertEqual(operation.migration_name_fragment, "alter_pony_managers")
        managers = project_state.models["test_almoma", "pony"].managers
        self.assertEqual(managers, [])

        new_state = project_state.clone()
        operation.state_forwards("test_almoma", new_state)
        self.assertIn(("test_almoma", "pony"), new_state.models)
        managers = new_state.models["test_almoma", "pony"].managers
        self.assertEqual(managers[0][0], "food_qs")
        self.assertIsInstance(managers[0][1], models.Manager)
        self.assertEqual(managers[1][0], "food_mgr")
        self.assertIsInstance(managers[1][1], FoodManager)
        self.assertEqual(managers[1][1].args, ("a", "b", 1, 2))
        self.assertEqual(managers[2][0], "food_mgr_kwargs")
        self.assertIsInstance(managers[2][1], FoodManager)
        self.assertEqual(managers[2][1].args, ("x", "y", 3, 4))
        rendered_state = new_state.apps
        model = rendered_state.get_model("test_almoma", "pony")
        self.assertIsInstance(model.food_qs, models.Manager)
        self.assertIsInstance(model.food_mgr, FoodManager)
        self.assertIsInstance(model.food_mgr_kwargs, FoodManager)