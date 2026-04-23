def test_add_constraint(self):
        project_state = self.set_up_test_model("test_addconstraint")
        gt_check = models.Q(pink__gt=2)
        gt_constraint = models.CheckConstraint(
            condition=gt_check, name="test_add_constraint_pony_pink_gt_2"
        )
        gt_operation = migrations.AddConstraint("Pony", gt_constraint)
        self.assertEqual(
            gt_operation.describe(),
            "Create constraint test_add_constraint_pony_pink_gt_2 on model Pony",
        )
        self.assertEqual(
            gt_operation.formatted_description(),
            "+ Create constraint test_add_constraint_pony_pink_gt_2 on model Pony",
        )
        self.assertEqual(
            gt_operation.migration_name_fragment,
            "pony_test_add_constraint_pony_pink_gt_2",
        )
        # Test the state alteration
        new_state = project_state.clone()
        gt_operation.state_forwards("test_addconstraint", new_state)
        self.assertEqual(
            len(new_state.models["test_addconstraint", "pony"].options["constraints"]),
            1,
        )
        Pony = new_state.apps.get_model("test_addconstraint", "Pony")
        self.assertEqual(len(Pony._meta.constraints), 1)
        # Test the database alteration
        with (
            CaptureQueriesContext(connection) as ctx,
            connection.schema_editor() as editor,
        ):
            gt_operation.database_forwards(
                "test_addconstraint", editor, project_state, new_state
            )
        if connection.features.supports_table_check_constraints:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pony.objects.create(pink=1, weight=1.0)
        else:
            self.assertIs(
                any("CHECK" in query["sql"] for query in ctx.captured_queries), False
            )
            Pony.objects.create(pink=1, weight=1.0)
        # Add another one.
        lt_check = models.Q(pink__lt=100)
        lt_constraint = models.CheckConstraint(
            condition=lt_check, name="test_add_constraint_pony_pink_lt_100"
        )
        lt_operation = migrations.AddConstraint("Pony", lt_constraint)
        lt_operation.state_forwards("test_addconstraint", new_state)
        self.assertEqual(
            len(new_state.models["test_addconstraint", "pony"].options["constraints"]),
            2,
        )
        Pony = new_state.apps.get_model("test_addconstraint", "Pony")
        self.assertEqual(len(Pony._meta.constraints), 2)
        with (
            CaptureQueriesContext(connection) as ctx,
            connection.schema_editor() as editor,
        ):
            lt_operation.database_forwards(
                "test_addconstraint", editor, project_state, new_state
            )
        if connection.features.supports_table_check_constraints:
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pony.objects.create(pink=100, weight=1.0)
        else:
            self.assertIs(
                any("CHECK" in query["sql"] for query in ctx.captured_queries), False
            )
            Pony.objects.create(pink=100, weight=1.0)
        # Test reversal
        with connection.schema_editor() as editor:
            gt_operation.database_backwards(
                "test_addconstraint", editor, new_state, project_state
            )
        Pony.objects.create(pink=1, weight=1.0)
        # Test deconstruction
        definition = gt_operation.deconstruct()
        self.assertEqual(definition[0], "AddConstraint")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2], {"model_name": "Pony", "constraint": gt_constraint}
        )