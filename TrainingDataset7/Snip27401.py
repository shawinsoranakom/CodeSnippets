def test_add_func_index(self):
        app_label = "test_addfuncin"
        index_name = f"{app_label}_pony_abs_idx"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(app_label)
        index = models.Index(Abs("weight"), name=index_name)
        operation = migrations.AddIndex("Pony", index)
        self.assertEqual(
            operation.describe(),
            "Create index test_addfuncin_pony_abs_idx on Abs(F(weight)) on model Pony",
        )
        self.assertEqual(
            operation.migration_name_fragment,
            "pony_test_addfuncin_pony_abs_idx",
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        self.assertEqual(len(new_state.models[app_label, "pony"].options["indexes"]), 1)
        self.assertIndexNameNotExists(table_name, index_name)
        # Add index.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexNameExists(table_name, index_name)
        # Reversal.
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        self.assertIndexNameNotExists(table_name, index_name)
        # Deconstruction.
        definition = operation.deconstruct()
        self.assertEqual(definition[0], "AddIndex")
        self.assertEqual(definition[1], [])
        self.assertEqual(definition[2], {"model_name": "Pony", "index": index})