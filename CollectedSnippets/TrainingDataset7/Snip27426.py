def test_alter_order_with_respect_to(self):
        """
        Tests the AlterOrderWithRespectTo operation.
        """
        project_state = self.set_up_test_model("test_alorwrtto", related_model=True)
        # Test the state alteration
        operation = migrations.AlterOrderWithRespectTo("Rider", "pony")
        self.assertEqual(
            operation.describe(), "Set order_with_respect_to on Rider to pony"
        )
        self.assertEqual(
            operation.formatted_description(),
            "~ Set order_with_respect_to on Rider to pony",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "alter_rider_order_with_respect_to",
        )
        new_state = project_state.clone()
        operation.state_forwards("test_alorwrtto", new_state)
        self.assertIsNone(
            project_state.models["test_alorwrtto", "rider"].options.get(
                "order_with_respect_to", None
            )
        )
        self.assertEqual(
            new_state.models["test_alorwrtto", "rider"].options.get(
                "order_with_respect_to", None
            ),
            "pony",
        )
        # Make sure there's no matching index
        self.assertColumnNotExists("test_alorwrtto_rider", "_order")
        # Create some rows before alteration
        rendered_state = project_state.apps
        pony = rendered_state.get_model("test_alorwrtto", "Pony").objects.create(
            weight=50
        )
        rider1 = rendered_state.get_model("test_alorwrtto", "Rider").objects.create(
            pony=pony
        )
        rider1.friend = rider1
        rider1.save()
        rider2 = rendered_state.get_model("test_alorwrtto", "Rider").objects.create(
            pony=pony
        )
        rider2.friend = rider2
        rider2.save()
        # Test the database alteration
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_alorwrtto", editor, project_state, new_state
            )
        self.assertColumnExists("test_alorwrtto_rider", "_order")
        # Check for correct value in rows
        updated_riders = new_state.apps.get_model(
            "test_alorwrtto", "Rider"
        ).objects.all()
        self.assertEqual(updated_riders[0]._order, 0)
        self.assertEqual(updated_riders[1]._order, 0)
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards(
                "test_alorwrtto", editor, new_state, project_state
            )
        self.assertColumnNotExists("test_alorwrtto_rider", "_order")
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AlterOrderWithRespectTo")
        self.assertEqual(definition[1], [])
        self.assertEqual(
            definition[2], {"name": "Rider", "order_with_respect_to": "pony"}
        )