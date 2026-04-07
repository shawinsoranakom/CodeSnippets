def test_delete_mti_model(self):
        project_state = self.set_up_test_model("test_dlmtimo", mti_model=True)
        # Test the state alteration
        operation = migrations.DeleteModel("ShetlandPony")
        new_state = project_state.clone()
        operation.state_forwards("test_dlmtimo", new_state)
        self.assertIn(("test_dlmtimo", "shetlandpony"), project_state.models)
        self.assertNotIn(("test_dlmtimo", "shetlandpony"), new_state.models)
        # Test the database alteration
        self.assertTableExists("test_dlmtimo_pony")
        self.assertTableExists("test_dlmtimo_shetlandpony")
        self.assertColumnExists("test_dlmtimo_shetlandpony", "pony_ptr_id")
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_dlmtimo", editor, project_state, new_state
            )
        self.assertTableExists("test_dlmtimo_pony")
        self.assertTableNotExists("test_dlmtimo_shetlandpony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_dlmtimo", editor, new_state, project_state
            )
        self.assertTableExists("test_dlmtimo_pony")
        self.assertTableExists("test_dlmtimo_shetlandpony")
        self.assertColumnExists("test_dlmtimo_shetlandpony", "pony_ptr_id")