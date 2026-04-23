def test_create_model_with_constraint(self):
        where = models.Q(pink__gt=2)
        check_constraint = models.CheckConstraint(
            condition=where, name="test_constraint_pony_pink_gt_2"
        )
        operation = migrations.CreateModel(
            "Pony",
            [
                ("id", models.AutoField(primary_key=True)),
                ("pink", models.IntegerField(default=3)),
            ],
            options={"constraints": [check_constraint]},
        )

        # Test the state alteration
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards("test_crmo", new_state)
        self.assertEqual(
            len(new_state.models["test_crmo", "pony"].options["constraints"]), 1
        )

        # Test database alteration
        self.assertTableNotExists("test_crmo_pony")
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crmo", editor, project_state, new_state)
        self.assertTableExists("test_crmo_pony")
        with connection.cursor() as cursor:
            with self.assertRaises(IntegrityError):
                cursor.execute("INSERT INTO test_crmo_pony (id, pink) VALUES (1, 1)")

        # Test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_crmo", editor, new_state, project_state)
        self.assertTableNotExists("test_crmo_pony")

        # Test deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "CreateModel")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2]["options"]["constraints"], [check_constraint])