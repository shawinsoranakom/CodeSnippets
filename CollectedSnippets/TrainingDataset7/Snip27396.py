def test_rename_index_unnamed_index_with_unique_index(self):
        app_label = "test_rninuniwui"
        project_state = self.set_up_test_model(
            app_label,
            multicol_index=True,
            unique_together=True,
        )
        table_name = app_label + "_pony"
        self.assertIndexNotExists(table_name, "new_pony_test_idx")
        operation = migrations.RenameIndex(
            "Pony", new_name="new_pony_test_idx", old_fields=["pink", "weight"]
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        # Rename index.
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexNameExists(table_name, "new_pony_test_idx")