def test_remove_covering_unique_constraint(self):
        app_label = "test_removecovering_uc"
        covering_unique_constraint = models.UniqueConstraint(
            fields=["pink"],
            name="covering_pink_constraint_rm",
            include=["weight"],
        )
        project_state = self.set_up_test_model(
            app_label, constraints=[covering_unique_constraint]
        )
        operation = migrations.RemoveConstraint("Pony", covering_unique_constraint.name)
        self.assertEqual(
            operation.describe(),
            "Remove constraint covering_pink_constraint_rm from model Pony",
        )
        # Remove constraint.
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(
            len(new_state.models[app_label, "pony"].options["constraints"]), 0
        )
        Pony = new_state.apps.get_model(app_label, "Pony")
        self.assertEqual(len(Pony._meta.constraints), 0)
        with (
            connection.schema_editor() as editor,
            CaptureQueriesContext(connection) as ctx,
        ):
            operation.database_forwards(app_label, editor, project_state, new_state)
        # Constraint doesn't work.
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=4.0).delete()
        if not connection.features.supports_covering_indexes:
            self.assertEqual(len(ctx), 0)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        if connection.features.supports_covering_indexes:
            with self.assertRaises(IntegrityError):
                Pony.objects.create(pink=1, weight=4.0)
        else:
            Pony.objects.create(pink=1, weight=4.0)
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RemoveConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "model_name": "Pony",
                "name": "covering_pink_constraint_rm",
            },
        )