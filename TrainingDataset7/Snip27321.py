def test_rename_model_with_self_referential_fk(self):
        """
        Tests the RenameModel operation on model with self referential FK.
        """
        project_state = self.set_up_test_model("test_rmwsrf", related_model=True)
        # Test the state alteration
        operation = migrations.RenameModel("Rider", "HorseRider")
        self.assertEqual(operation.describe(), "Rename model Rider to HorseRider")
        new_state = project_state.clone()
        operation.state_forwards("test_rmwsrf", new_state)
        self.assertNotIn(("test_rmwsrf", "rider"), new_state.models)
        self.assertIn(("test_rmwsrf", "horserider"), new_state.models)
        # Remember, RenameModel also repoints all incoming FKs and M2Ms
        self.assertEqual(
            "self",
            new_state.models["test_rmwsrf", "horserider"]
            .fields["friend"]
            .remote_field.model,
        )
        HorseRider = new_state.apps.get_model("test_rmwsrf", "horserider")
        self.assertIs(
            HorseRider._meta.get_field("horserider").remote_field.model, HorseRider
        )
        # Test the database alteration
        self.assertTableExists("test_rmwsrf_rider")
        self.assertTableNotExists("test_rmwsrf_horserider")
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                "test_rmwsrf_rider", ["friend_id"], ("test_rmwsrf_rider", "id")
            )
            self.assertFKNotExists(
                "test_rmwsrf_rider", ["friend_id"], ("test_rmwsrf_horserider", "id")
            )
        with connection.schema_editor() as editor:
            operation.database_forwards("test_rmwsrf", editor, project_state, new_state)
        self.assertTableNotExists("test_rmwsrf_rider")
        self.assertTableExists("test_rmwsrf_horserider")
        if connection.features.supports_foreign_keys:
            self.assertFKNotExists(
                "test_rmwsrf_horserider", ["friend_id"], ("test_rmwsrf_rider", "id")
            )
            self.assertFKExists(
                "test_rmwsrf_horserider",
                ["friend_id"],
                ("test_rmwsrf_horserider", "id"),
            )
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_rmwsrf", editor, new_state, project_state
            )
        self.assertTableExists("test_rmwsrf_rider")
        self.assertTableNotExists("test_rmwsrf_horserider")
        if connection.features.supports_foreign_keys:
            self.assertFKExists(
                "test_rmwsrf_rider", ["friend_id"], ("test_rmwsrf_rider", "id")
            )
            self.assertFKNotExists(
                "test_rmwsrf_rider", ["friend_id"], ("test_rmwsrf_horserider", "id")
            )