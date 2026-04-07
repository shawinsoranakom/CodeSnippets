def test_add_index(self):
        """
        Test the AddIndex operation.
        """
        project_state = self.set_up_test_model("test_adin")
        msg = (
            "Indexes passed to AddIndex operations require a name argument. "
            "<Index: fields=['pink']> doesn't have one."
        )
        with self.assertRaisesMessage(ValueError, msg):
            migrations.AddIndex("Pony", models.Index(fields=["pink"]))
        index = models.Index(fields=["pink"], name="test_adin_pony_pink_idx")
        operation = migrations.AddIndex("Pony", index)
        self.assertEqual(
            operation.describe(),
            "Create index test_adin_pony_pink_idx on field(s) pink of model Pony",
        )
        self.assertEqual(
            operation.formatted_description(),
            "+ Create index test_adin_pony_pink_idx on field(s) pink of model Pony",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "pony_test_adin_pony_pink_idx",
        )
        new_state = project_state.clone()
        operation.state_forwards("test_adin", new_state)
        # Test the database alteration
        self.assertEqual(
            len(new_state.models["test_adin", "pony"].options["indexes"]), 1
        )
        self.assertIndexNotExists("test_adin_pony", ["pink"])
        with connection.schema_editor() as editor:
            operation.database_forwards("test_adin", editor, project_state, new_state)
        self.assertIndexExists("test_adin_pony", ["pink"])
        # And test reversal
        with connection.schema_editor() as editor:
            operation.database_backwards("test_adin", editor, new_state, project_state)
        self.assertIndexNotExists("test_adin_pony", ["pink"])
        # And deconstruction
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AddIndex")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"model_name": "Pony", "index": index})