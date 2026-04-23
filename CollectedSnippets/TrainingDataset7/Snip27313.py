def test_create_model_with_deferred_unique_constraint(self):
        deferred_unique_constraint = models.UniqueConstraint(
            fields=["pink"],
            name="deferrable_pink_constraint",
            deferrable=models.Deferrable.DEFERRED,
        )
        operation = migrations.CreateModel(
            "Pony",
            [
                ("id", models.AutoField(primary_key=True)),
                ("pink", models.IntegerField(default=3)),
            ],
            options={"constraints": [deferred_unique_constraint]},
        )
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards("test_crmo", new_state)
        self.assertEqual(
            len(new_state.models["test_crmo", "pony"].options["constraints"]), 1
        )
        self.assertTableNotExists("test_crmo_pony")
        # Create table.
        with connection.schema_editor() as editor:
            operation.database_forwards("test_crmo", editor, project_state, new_state)
        self.assertTableExists("test_crmo_pony")
        Pony = new_state.apps.get_model("test_crmo", "Pony")
        Pony.objects.create(pink=1)
        if connection.features.supports_deferrable_unique_constraints:
            # Unique constraint is deferred.
            with transaction.atomic():
                obj = Pony.objects.create(pink=1)
                obj.pink = 2
                obj.save()
            # Constraint behavior can be changed with SET CONSTRAINTS.
            with self.assertRaises(IntegrityError):
                with transaction.atomic(), connection.cursor() as cursor:
                    quoted_name = connection.ops.quote_name(
                        deferred_unique_constraint.name
                    )
                    cursor.execute("SET CONSTRAINTS %s IMMEDIATE" % quoted_name)
                    obj = Pony.objects.create(pink=1)
                    obj.pink = 3
                    obj.save()
        else:
            Pony.objects.create(pink=1)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards("test_crmo", editor, new_state, project_state)
        self.assertTableNotExists("test_crmo_pony")
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "CreateModel")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2]["options"]["constraints"],
            [deferred_unique_constraint],
        )