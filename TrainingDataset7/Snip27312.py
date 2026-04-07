def test_create_model_with_partial_unique_constraint(self):
        partial_unique_constraint = models.UniqueConstraint(
            fields=["pink"],
            condition=models.Q(weight__gt=5),
            name="test_constraint_pony_pink_for_weight_gt_5_uniq",
        )
        operation = migrations.CreateModel(
            "Pony",
            [
                ("id", models.AutoField(primary_key=True)),
                ("pink", models.IntegerField(default=3)),
                ("weight", models.FloatField()),
            ],
            options={"constraints": [partial_unique_constraint]},
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
        # Test constraint works
        Pony = new_state.apps.get_model("test_crmo", "Pony")
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=6.0)
        if connection.features.supports_partial_indexes:
            with self.assertRaises(IntegrityError):
                Pony.objects.create(pink=1, weight=7.0)
        else:
            Pony.objects.create(pink=1, weight=7.0)
        # Test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_crmo", editor, new_state, project_state)
        self.assertTableNotExists("test_crmo_pony")
        # Test deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "CreateModel")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2]["options"]["constraints"], [partial_unique_constraint]
        )