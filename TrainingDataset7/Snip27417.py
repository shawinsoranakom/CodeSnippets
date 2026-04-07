def test_add_deferred_unique_constraint(self):
        app_label = "test_adddeferred_uc"
        project_state = self.set_up_test_model(app_label)
        deferred_unique_constraint = models.UniqueConstraint(
            fields=["pink"],
            name="deferred_pink_constraint_add",
            deferrable=models.Deferrable.DEFERRED,
        )
        operation = migrations.AddConstraint("Pony", deferred_unique_constraint)
        self.assertEqual(
            operation.describe(),
            "Create constraint deferred_pink_constraint_add on model Pony",
        )
        # Add constraint.
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(
            len(new_state.models[app_label, "pony"].options["constraints"]), 1
        )
        Pony = new_state.apps.get_model(app_label, "Pony")
        self.assertEqual(len(Pony._meta.constraints), 1)
        with (
            connection.schema_editor() as editor,
            CaptureQueriesContext(connection) as ctx,
        ):
            operation.database_forwards(app_label, editor, project_state, new_state)
        Pony.objects.create(pink=1, weight=4.0)
        if connection.features.supports_deferrable_unique_constraints:
            # Unique constraint is deferred.
            with transaction.atomic():
                obj = Pony.objects.create(pink=1, weight=4.0)
                obj.pink = 2
                obj.save()
            # Constraint behavior can be changed with SET CONSTRAINTS.
            with self.assertRaises(IntegrityError):
                with transaction.atomic(), connection.cursor() as cursor:
                    quoted_name = connection.ops.quote_name(
                        deferred_unique_constraint.name
                    )
                    cursor.execute("SET CONSTRAINTS %s IMMEDIATE" % quoted_name)
                    obj = Pony.objects.create(pink=1, weight=4.0)
                    obj.pink = 3
                    obj.save()
        else:
            self.assertEqual(len(ctx), 0)
            Pony.objects.create(pink=1, weight=4.0)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        # Constraint doesn't work.
        Pony.objects.create(pink=1, weight=4.0)
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AddConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {"model_name": "Pony", "constraint": deferred_unique_constraint},
        )