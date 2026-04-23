def test_add_func_unique_constraint(self):
        app_label = "test_adfuncuc"
        constraint_name = f"{app_label}_pony_abs_uq"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        constraint = models.UniqueConstraint(Abs("weight"), name=constraint_name)
        operation = migrations.AddConstraint("Pony", constraint)
        self.assertEqual(
            operation.describe(),
            "Create constraint test_adfuncuc_pony_abs_uq on model Pony",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "pony_test_adfuncuc_pony_abs_uq",
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(
            len(new_state.models[app_label, "pony"].options["constraints"]), 1
        )
        self.assertIndexNameNotExists(table_name, constraint_name)
        # Add constraint.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        Pony = new_state.apps.get_model(app_label, "Pony")
        Pony.objects.create(weight=4.0)
        if connection.features.supports_expression_indexes:
            self.assertIndexNameExists(table_name, constraint_name)
            with self.assertRaises(IntegrityError):
                Pony.objects.create(weight=-4.0)
        else:
            self.assertIndexNameNotExists(table_name, constraint_name)
            Pony.objects.create(weight=-4.0)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertIndexNameNotExists(table_name, constraint_name)
        # Constraint doesn't work.
        Pony.objects.create(weight=-4.0)
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AddConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {"model_name": "Pony", "constraint": constraint},
        )