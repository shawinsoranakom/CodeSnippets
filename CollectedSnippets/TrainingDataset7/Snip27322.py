def test_rename_model_with_superclass_fk(self):
        """
        Tests the RenameModel operation on a model which has a superclass that
        has a foreign key.
        """
        project_state = self.set_up_test_model(
            "test_rmwsc", related_model=True, mti_model=True
        )
        # Test the state alteration
        operation = migrations.RenameModel("ShetlandPony", "LittleHorse")
        self.assertEqual(
            operation.describe(), "Rename model ShetlandPony to LittleHorse"
        )
        new_state = project_state.clone()
        operation.state_forwards("test_rmwsc", new_state)
        self.assertNotIn(("test_rmwsc", "shetlandpony"), new_state.models)
        self.assertIn(("test_rmwsc", "littlehorse"), new_state.models)
        # RenameModel shouldn't repoint the superclass's relations, only local
        # ones
        self.assertEqual(
            project_state.models["test_rmwsc", "rider"]
            .fields["pony"]
            .remote_field.model,
            new_state.models["test_rmwsc", "rider"].fields["pony"].remote_field.model,
        )
        # Before running the migration we have a table for Shetland Pony, not
        # Little Horse.
        self.assertTableExists("test_rmwsc_shetlandpony")
        self.assertTableNotExists("test_rmwsc_littlehorse")
        if connection.features.supports_foreign_keys:
            # and the foreign key on rider points to pony, not shetland pony
            self.assertFKExists(
                "test_rmwsc_rider", ["pony_id"], ("test_rmwsc_pony", "id")
            )
            self.assertFKNotExists(
                "test_rmwsc_rider", ["pony_id"], ("test_rmwsc_shetlandpony", "id")
            )
        with connection.schema_editor() as editor:
            operation.database_forwards("test_rmwsc", editor, project_state, new_state)
        # Now we have a little horse table, not shetland pony
        self.assertTableNotExists("test_rmwsc_shetlandpony")
        self.assertTableExists("test_rmwsc_littlehorse")
        if connection.features.supports_foreign_keys:
            # but the Foreign keys still point at pony, not little horse
            self.assertFKExists(
                "test_rmwsc_rider", ["pony_id"], ("test_rmwsc_pony", "id")
            )
            self.assertFKNotExists(
                "test_rmwsc_rider", ["pony_id"], ("test_rmwsc_littlehorse", "id")
            )