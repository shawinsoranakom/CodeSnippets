def test_create_ignore_swapped(self):
        """
        The CreateTable operation ignores swapped models.
        """
        operation = migrations.CreateModel(
            "Pony",
            [
                ("id", models.AutoField(primary_key=True)),
                ("pink", models.IntegerField(default=1)),
            ],
            options={
                "swappable": "TEST_SWAP_MODEL",
            },
        )
        # Test the state alteration (it should still be there!)
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards("test_crigsw", new_state)
        self.assertEqual(new_state.models["test_crigsw", "pony"].name, "Pony")
        self.assertEqual(len(new_state.models["test_crigsw", "pony"].fields), 2)
        # Test the database alteration
        self.assertTableNotExists("test_crigsw_pony")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crigsw", editor, project_state, new_state)
        self.assertTableNotExists("test_crigsw_pony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_crigsw", editor, new_state, project_state
            )
        self.assertTableNotExists("test_crigsw_pony")