def test_remove_func_unique_constraint(self):
        app_label = "test_rmfuncuc"
        constraint_name = f"{app_label}_pony_abs_uq"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(
            app_label,
            constraints=[
                models.UniqueConstraint(Abs("weight"), name=constraint_name),
            ],
        )
        self.assertTableExists(table_name)
        if connection.features.supports_expression_indexes:
            self.assertIndexNameExists(table_name, constraint_name)
        operation = migrations.RemoveConstraint("Pony", constraint_name)
        self.assertEqual(
            operation.describe(),
            "Remove constraint test_rmfuncuc_pony_abs_uq from model Pony",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "remove_pony_test_rmfuncuc_pony_abs_uq",
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(
            len(new_state.models[app_label, "pony"].options["constraints"]), 0
        )
        Pony = new_state.apps.get_model(app_label, "Pony")
        self.assertEqual(len(Pony._meta.constraints), 0)
        # Remove constraint.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexNameNotExists(table_name, constraint_name)
        # Constraint doesn't work.
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=-4.0).delete()
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        if connection.features.supports_expression_indexes:
            self.assertIndexNameExists(table_name, constraint_name)
            with self.assertRaises(IntegrityError):
                Pony.objects.create(weight=-4.0)
        else:
            self.assertIndexNameNotExists(table_name, constraint_name)
            Pony.objects.create(weight=-4.0)
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "RemoveConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"model_name": "Pony", "name": constraint_name})