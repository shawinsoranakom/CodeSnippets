def test_alter_constraint(self):
        constraint = models.UniqueConstraint(
            fields=["pink"], name="test_alter_constraint_pony_fields_uq"
        )
        project_state = self.set_up_test_model(
            "test_alterconstraint", constraints=[constraint]
        )

        new_state = project_state.clone()
        violation_error_message = "Pink isn't unique"
        uq_constraint = models.UniqueConstraint(
            fields=["pink"],
            name="test_alter_constraint_pony_fields_uq",
            violation_error_message=violation_error_message,
        )
        uq_operation = migrations.AlterConstraint(
            "Pony", "test_alter_constraint_pony_fields_uq", uq_constraint
        )
        self.assertEqual(
            uq_operation.describe(),
            "Alter constraint test_alter_constraint_pony_fields_uq on Pony",
        )
        self.assertEqual(
            uq_operation.formatted_description(),
            "~ Alter constraint test_alter_constraint_pony_fields_uq on Pony",
        )
        self.assertEqual(
            uq_operation.migration_name_fragment,
            "alter_pony_test_alter_constraint_pony_fields_uq",
        )

        uq_operation.state_forwards("test_alterconstraint", new_state)
        self.assertEqual(
            project_state.models["test_alterconstraint", "pony"]
            .options["constraints"][0]
            .violation_error_message,
            "Constraint “%(name)s” is violated.",
        )
        self.assertEqual(
            new_state.models["test_alterconstraint", "pony"]
            .options["constraints"][0]
            .violation_error_message,
            violation_error_message,
        )

        with connection.schema_editor() as editor, self.assertNumQueries(0):
            uq_operation.database_forwards(
                "test_alterconstraint", editor, project_state, new_state
            )
        self.assertConstraintExists(
            "test_alterconstraint_pony",
            "test_alter_constraint_pony_fields_uq",
            value=False,
        )
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            uq_operation.database_backwards(
                "test_alterconstraint", editor, project_state, new_state
            )
        self.assertConstraintExists(
            "test_alterconstraint_pony",
            "test_alter_constraint_pony_fields_uq",
            value=False,
        )
        definition = uq_operation.deconstruct()
        self.assertEqual(definition[0], "AlterConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "model_name": "Pony",
                "name": "test_alter_constraint_pony_fields_uq",
                "constraint": uq_constraint,
            },
        )