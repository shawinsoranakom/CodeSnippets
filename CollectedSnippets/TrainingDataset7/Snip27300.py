def test_create_model(self):
        """
        Tests the CreateModel operation.
        Most other tests use this operation as part of setup, so check failures
        here first.
        """
        operation = migrations.CreateModel(
            "Pony",
            [
                ("id", models.AutoField(primary_key=True)),
                ("pink", models.IntegerField(default=1)),
            ],
        )
        self.assertEqual(operation.describe(), "Create model Pony")
        self.assertEqual(operation.formatted_description(), "+ Create model Pony")
        self.assertEqual(operation.migration_name_fragment, "pony")
        # Test the state alteration
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards("test_crmo", new_state)
        self.assertEqual(new_state.models["test_crmo", "pony"].name, "Pony")
        self.assertEqual(len(new_state.models["test_crmo", "pony"].fields), 2)
        # Test the database alteration
        self.assertTableNotExists("test_crmo_pony")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crmo", editor, project_state, new_state)
        self.assertTableExists("test_crmo_pony")
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_crmo", editor, new_state, project_state)
        self.assertTableNotExists("test_crmo_pony")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "CreateModel")
        self.assertEqual(definition[1], [])
        self.assertEqual(sorted(definition[2]), ["fields", "name"])
        # And default manager not in set
        operation = migrations.CreateModel(
            "Foo", fields=[], managers=[("objects", models.Manager())]
        )
        definition = operation.deconstruct()
        self.assertNotIn("managers", definition[2])