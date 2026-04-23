def test_remove_partial_unique_constraint(self):
        project_state = self.set_up_test_model(
            "test_removepartialuniqueconstraint",
            constraints=[
                models.UniqueConstraint(
                    fields=["pink"],
                    condition=models.Q(weight__gt=5),
                    name="test_constraint_pony_pink_for_weight_gt_5_uniq",
                ),
            ],
        )
        gt_operation = migrations.RemoveConstraint(
            "Pony", "test_constraint_pony_pink_for_weight_gt_5_uniq"
        )
        self.assertEqual(
            gt_operation.describe(),
            "Remove constraint test_constraint_pony_pink_for_weight_gt_5_uniq from "
            "model Pony",
        )
        # Test state alteration
        new_state = project_state.clone()
        gt_operation.state_forwards("test_removepartialuniqueconstraint", new_state)
        self.assertEqual(
            len(
                new_state.models["test_removepartialuniqueconstraint", "pony"].options[
                    "constraints"
                ]
            ),
            0,
        )
        Pony = new_state.apps.get_model("test_removepartialuniqueconstraint", "Pony")
        self.assertEqual(len(Pony._meta.constraints), 0)
        # Test database alteration
        with connection.schema_editor() as editor:
            gt_operation.database_forwards(
                "test_removepartialuniqueconstraint", editor, project_state, new_state
            )
        # Test constraint doesn't work
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=6.0)
        Pony.objects.create(pink=1, weight=7.0).delete()
        # Test reversal
        with connection.schema_editor() as editor:
            gt_operation.database_backwards(
                "test_removepartialuniqueconstraint", editor, new_state, project_state
            )
        # Test constraint works
        if connection.features.supports_partial_indexes:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pony.objects.create(pink=1, weight=7.0)
        else:
            Pony.objects.create(pink=1, weight=7.0)
        # Test deconstruction
        definition = gt_operation.deconstruct()
        self.assertEqual(definition[0], "RemoveConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {
                "model_name": "Pony",
                "name": "test_constraint_pony_pink_for_weight_gt_5_uniq",
            },
        )