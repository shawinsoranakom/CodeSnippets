def test_validate(self):
        constraint_name = "pony_pink_gte_check"
        constraint = CheckConstraint(condition=Q(pink__gte=4), name=constraint_name)
        operation = AddConstraintNotValid("Pony", constraint=constraint)
        project_state, new_state = self.make_test_state(self.app_label, operation)
        Pony = new_state.apps.get_model(self.app_label, "Pony")
        obj = Pony.objects.create(pink=2, weight=1.0)
        # Add constraint.
        with connection.schema_editor(atomic=True) as editor:
            operation.database_forwards(
                self.app_label, editor, project_state, new_state
            )
        project_state = new_state
        new_state = new_state.clone()
        operation = ValidateConstraint("Pony", name=constraint_name)
        operation.state_forwards(self.app_label, new_state)
        self.assertEqual(
            operation.describe(),
            f"Validate constraint {constraint_name} on model Pony",
        )
        self.assertEqual(
            operation.formatted_description(),
            f"~ Validate constraint {constraint_name} on model Pony",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            f"pony_validate_{constraint_name}",
        )
        # Validate constraint.
        with connection.schema_editor(atomic=True) as editor:
            msg = f'check constraint "{constraint_name}"'
            with self.assertRaisesMessage(IntegrityError, msg):
                operation.database_forwards(
                    self.app_label, editor, project_state, new_state
                )
        obj.pink = 5
        obj.save()
        with connection.schema_editor(atomic=True) as editor:
            operation.database_forwards(
                self.app_label, editor, project_state, new_state
            )
        # Reversal is a noop.
        with connection.schema_editor() as editor:
            with self.assertNumQueries(0):
                operation.database_backwards(
                    self.app_label, editor, new_state, project_state
                )
        # Deconstruction.
        name, args, kwargs = operation.deconstruct()
        self.assertEqual(name, "ValidateConstraint")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"model_name": "Pony", "name": constraint_name})