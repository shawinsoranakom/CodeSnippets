def test_alter_model_options_emptying(self):
        """
        The AlterModelOptions operation removes keys from the dict (#23121)
        """
        project_state = self.set_up_test_model("test_almoop", options=True)
        # Test the state alteration (no DB alteration to test)
        operation = migrations.AlterModelOptions("Pony", {})
        self.assertEqual(operation.describe(), "Change Meta options on Pony")
        new_state = project_state.clone()
        operation.state_forwards("test_almoop", new_state)
        self.assertEqual(
            len(
                project_state.models["test_almoop", "pony"].options.get(
                    "permissions", []
                )
            ),
            1,
        )
        self.assertEqual(
            len(new_state.models["test_almoop", "pony"].options.get("permissions", [])),
            0,
        )
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterModelOptions")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"name": "Pony", "options": {}})