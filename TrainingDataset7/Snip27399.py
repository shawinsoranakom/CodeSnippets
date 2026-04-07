def test_rename_index_state_forwards(self):
        app_label = "test_rnidsf"
        project_state = self.set_up_test_model(app_label, index=True)
        old_model = project_state.apps.get_model(app_label, "Pony")
        new_state = project_state.clone()

        operation = migrations.RenameIndex(
            "Pony", new_name="new_pony_pink_idx", old_name="pony_pink_idx"
        )
        operation.state_forwards(app_label, new_state)
        new_model = new_state.apps.get_model(app_label, "Pony")
        self.assertIsNot(old_model, new_model)
        self.assertEqual(new_model._meta.indexes[0].name, "new_pony_pink_idx")