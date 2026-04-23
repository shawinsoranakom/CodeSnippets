def test_rename_missing_field(self):
        state = ProjectState()
        state.add_model(ModelState("app", "model", []))
        with self.assertRaisesMessage(
            FieldDoesNotExist, "app.model has no field named 'field'"
        ):
            migrations.RenameField("model", "field", "new_field").state_forwards(
                "app", state
            )