def test_alter_model_options(self):
        """
        Tests the AlterModelOptions operation.
        """
        project_state = self.set_up_test_model("test_almoop")
        # Test the state alteration (no DB alteration to test)
        operation = migrations.AlterModelOptions(
            "Pony", {"permissions": [("can_groom", "Can groom")]}
        )
        self.assertEqual(operation.describe(), "Change Meta options on Pony")
        self.assertEqual(
            operation.formatted_description(), "~ Change Meta options on Pony"
        )
        self.assertEqual(operation.migration_name_fragment, "alter_pony_options")
        new_state = project_state.clone()
        operation.state_forwards("test_almoop", new_state)
        self.assertEqual(
            len(
                project_state.models["test_almoop", "pony"].options.get(
                    "permissions", []
                )
            ),
            0,
        )
        self.assertEqual(
            len(new_state.models["test_almoop", "pony"].options.get("permissions", [])),
            1,
        )
        self.assertEqual(
            new_state.models["test_almoop", "pony"].options["permissions"][0][0],
            "can_groom",
        )
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterModelOptions")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {"name": "Pony", "options": {"permissions": [("can_groom", "Can groom")]}},
        )