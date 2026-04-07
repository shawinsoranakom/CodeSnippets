def test_add_partial_unique_constraint(self):
        project_state = self.set_up_test_model("test_addpartialuniqueconstraint")
        partial_unique_constraint = models.UniqueConstraint(
            fields=["pink"],
            condition=models.Q(weight__gt=5),
            name="test_constraint_pony_pink_for_weight_gt_5_uniq",
        )
        operation = migrations.AddConstraint("Pony", partial_unique_constraint)
        self.assertEqual(
            operation.describe(),
            "Create constraint test_constraint_pony_pink_for_weight_gt_5_uniq "
            "on model Pony",
        )
        # Test the state alteration
        new_state = project_state.clone()
        operation.state_forwards("test_addpartialuniqueconstraint", new_state)
        self.assertEqual(
            len(
                new_state.models["test_addpartialuniqueconstraint", "pony"].options[
                    "constraints"
                ]
            ),
            1,
        )
        Pony = new_state.apps.get_model("test_addpartialuniqueconstraint", "Pony")
        self.assertEqual(len(Pony._meta.constraints), 1)
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_addpartialuniqueconstraint", editor, project_state, new_state
            )
        # Test constraint works
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=4.0)
        Pony.objects.create(pink=1, weight=6.0)
        if connection.features.supports_partial_indexes:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pony.objects.create(pink=1, weight=7.0)
        else:
            Pony.objects.create(pink=1, weight=7.0)
        # Test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_addpartialuniqueconstraint", editor, new_state, project_state
            )
        # Test constraint doesn't work
        Pony.objects.create(pink=1, weight=7.0)
        # Test deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AddConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2],
            {"model_name": "Pony", "constraint": partial_unique_constraint},
        )