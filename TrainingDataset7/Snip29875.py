def test_add(self):
        project_state = self.set_up_test_model(self.app_label, index=False)
        table_name = "%s_pony" % self.app_label
        index = Index(fields=["pink"], name="pony_pink_idx")
        new_state = project_state.clone()
        operation = AddIndexConcurrently("Pony", index)
        self.assertEqual(
            operation.describe(),
            "Concurrently create index pony_pink_idx on field(s) pink of model Pony",
        )
        self.assertEqual(
            operation.formatted_description(),
            "+ Concurrently create index pony_pink_idx on field(s) pink of model Pony",
        )
        operation.state_forwards(self.app_label, new_state)
        self.assertEqual(
            len(new_state.models[self.app_label, "pony"].options["indexes"]), 1
        )
        self.assertIndexNotExists(table_name, ["pink"])
        # Add index.
        with connection.schema_editor(atomic=False) as editor:
            operation.database_forwards(
                self.app_label, editor, project_state, new_state
            )
        self.assertIndexExists(table_name, ["pink"])
        # Reversal.
        with connection.schema_editor(atomic=False) as editor:
            operation.database_backwards(
                self.app_label, editor, new_state, project_state
            )
        self.assertIndexNotExists(table_name, ["pink"])
        # Deconstruction.
        name, args, kwargs = operation.deconstruct()
        self.assertEqual(name, "AddIndexConcurrently")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"model_name": "Pony", "index": index})