def test_rename_index_unknown_unnamed_index(self):
        app_label = "test_rninuui"
        project_state = self.set_up_test_model(app_label)
        operation = migrations.RenameIndex(
            "Pony", new_name="new_pony_test_idx", old_fields=("weight", "pink")
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        msg = "Found wrong number (0) of indexes for test_rninuui_pony(weight, pink)."
        with connection.schema_editor() as editor:
            with self.assertRaisesMessage(ValueError, msg):
                operation.database_forwards(app_label, editor, project_state, new_state)