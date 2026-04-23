def test_rename_model(self):
        """
        Tests the RenameModel operation.
        """
        project_state = self.set_up_test_model("test_rnmo", related_model=True)
        # Test the state alteration
        operation = migrations.RenameModel("Pony", "Horse")
        self.assertEqual(operation.describe(), "Rename model Pony to Horse")
        self.assertEqual(
            operation.formatted_description(), "~ Rename model Pony to Horse"
        )
        self.assertEqual(operation.migration_name_fragment, "rename_pony_horse")
        # Test initial state and database
        self.assertIn(("test_rnmo", "pony"), project_state.models)
        self.assertNotIn(("test_rnmo", "horse"), project_state.models)
        self.assertTableExists("test_rnmo_pony")
        self.assertTableNotExists("test_rnmo_horse")
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                "test_rnmo_rider", ["pony_id"], ("test_rnmo_pony", "id")
            )
            self.assertFKNotExists(
                "test_rnmo_rider", ["pony_id"], ("test_rnmo_horse", "id")
            )
        # Migrate forwards
        new_state = project_state.clone()
        new_state = self.apply_operations("test_rnmo", new_state, [operation])
        # Test new state and database
        self.assertNotIn(("test_rnmo", "pony"), new_state.models)
        self.assertIn(("test_rnmo", "horse"), new_state.models)
        # RenameModel also repoints all incoming FKs and M2Ms
        self.assertEqual(
            new_state.models["test_rnmo", "rider"].fields["pony"].remote_field.model,
            "test_rnmo.Horse",
        )
        self.assertTableNotExists("test_rnmo_pony")
        self.assertTableExists("test_rnmo_horse")
        if connection.features.supports_foreign_keys:
            self.assertFKNotExists(
                "test_rnmo_rider", ["pony_id"], ("test_rnmo_pony", "id")
            )
            self.assertFKExists(
                "test_rnmo_rider", ["pony_id"], ("test_rnmo_horse", "id")
            )
        # Migrate backwards
        original_state = self.unapply_operations(
            "test_rnmo", project_state, [operation]
        )
        # Test original state and database
        self.assertIn(("test_rnmo", "pony"), original_state.models)
        self.assertNotIn(("test_rnmo", "horse"), original_state.models)
        self.assertEqual(
            original_state.models["test_rnmo", "rider"]
            .fields["pony"]
            .remote_field.model,
            "Pony",
        )
        self.assertTableExists("test_rnmo_pony")
        self.assertTableNotExists("test_rnmo_horse")
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                "test_rnmo_rider", ["pony_id"], ("test_rnmo_pony", "id")
            )
            self.assertFKNotExists(
                "test_rnmo_rider", ["pony_id"], ("test_rnmo_horse", "id")
            )
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RenameModel")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"old_name": "Pony", "new_name": "Horse"})