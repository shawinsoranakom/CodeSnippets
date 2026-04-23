def test_create_proxy_model(self):
        """
        CreateModel ignores proxy models.
        """
        project_state = self.set_up_test_model("test_crprmo")
        # Test the state alteration
        operation = migrations.CreateModel(
            "ProxyPony",
            [],
            options={"proxy": True},
            bases=("test_crprmo.Pony",),
        )
        self.assertEqual(operation.describe(), "Create proxy model ProxyPony")
        new_state = project_state.clone()
        operation.state_forwards("test_crprmo", new_state)
        self.assertIn(("test_crprmo", "proxypony"), new_state.models)
        # Test the database alteration
        self.assertTableNotExists("test_crprmo_proxypony")
        self.assertTableExists("test_crprmo_pony")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crprmo", editor, project_state, new_state)
        self.assertTableNotExists("test_crprmo_proxypony")
        self.assertTableExists("test_crprmo_pony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_crprmo", editor, new_state, project_state
            )
        self.assertTableNotExists("test_crprmo_proxypony")
        self.assertTableExists("test_crprmo_pony")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "CreateModel")
        self.assertEqual(definition[1], [])
        self.assertEqual(sorted(definition[2]), ["bases", "fields", "name", "options"])