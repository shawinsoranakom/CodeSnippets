def test_remove_constraint(self):
        project_state = self.set_up_test_model(
            "test_removeconstraint",
            constraints=[
                models.CheckConstraint(
                    condition=models.Q(pink__gt=2),
                    name="test_remove_constraint_pony_pink_gt_2",
                ),
                models.CheckConstraint(
                    condition=models.Q(pink__lt=100),
                    name="test_remove_constraint_pony_pink_lt_100",
                ),
            ],
        )
        gt_operation = migrations.RemoveConstraint(
            "Pony", "test_remove_constraint_pony_pink_gt_2"
        )
        self.assertEqual(
            gt_operation.describe(),
            "Remove constraint test_remove_constraint_pony_pink_gt_2 from model Pony",
        )
        self.assertEqual(
            gt_operation.formatted_description(),
            "- Remove constraint test_remove_constraint_pony_pink_gt_2 from model Pony",
        )
        self.assertEqual(
            gt_operation.migration_name_fragment,
            "remove_pony_test_remove_constraint_pony_pink_gt_2",
        )
        # Test state alteration
        new_state = project_state.clone()
        gt_operation.state_forwards("test_removeconstraint", new_state)
        self.assertEqual(
            len(
                new_state.models["test_removeconstraint", "pony"].options["constraints"]
            ),
            1,
        )
        Pony = new_state.apps.get_model("test_removeconstraint", "Pony")
        self.assertEqual(len(Pony._meta.constraints), 1)
        # Test database alteration
        with connection.schema_editor() as editor:
            gt_operation.database_forwards(
                "test_removeconstraint", editor, project_state, new_state
            )
        Pony.objects.create(pink=1, weight=1.0).delete()
        if connection.features.supports_table_check_constraints:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pony.objects.create(pink=100, weight=1.0)
        else:
            Pony.objects.create(pink=100, weight=1.0)
        # Remove the other one.
        lt_operation = migrations.RemoveConstraint(
            "Pony", "test_remove_constraint_pony_pink_lt_100"
        )
        lt_operation.state_forwards("test_removeconstraint", new_state)
        self.assertEqual(
            len(
                new_state.models["test_removeconstraint", "pony"].options["constraints"]
            ),
            0,
        )
        Pony = new_state.apps.get_model("test_removeconstraint", "Pony")
        self.assertEqual(len(Pony._meta.constraints), 0)
        with connection.schema_editor() as editor:
            lt_operation.database_forwards(
                "test_removeconstraint", editor, project_state, new_state
            )
        Pony.objects.create(pink=100, weight=1.0).delete()
        # Test reversal
        with connection.schema_editor() as editor:
            gt_operation.database_backwards(
                "test_removeconstraint", editor, new_state, project_state
            )
        if connection.features.supports_table_check_constraints:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pony.objects.create(pink=1, weight=1.0)
        else:
            Pony.objects.create(pink=1, weight=1.0)
        # Test deconstruction
        definition = gt_operation.deconstruct()
        self.assertEqual(definition[0], "RemoveConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {"model_name": "Pony", "name": "test_remove_constraint_pony_pink_gt_2"},
        )