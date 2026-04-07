def test_alter_id_pk_to_uuid_pk(self):
        app_label = "test_alidpktuuidpk"
        project_state = self.set_up_test_model(app_label)
        new_state = project_state.clone()
        # Add UUID field.
        operation = migrations.AddField("Pony", "uuid", models.UUIDField())
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        # Remove ID.
        project_state = new_state
        new_state = new_state.clone()
        operation = migrations.RemoveField("Pony", "id")
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnNotExists(f"{app_label}_pony", "id")
        # Rename to ID.
        project_state = new_state
        new_state = new_state.clone()
        operation = migrations.RenameField("Pony", "uuid", "id")
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertColumnNotExists(f"{app_label}_pony", "uuid")
        self.assertColumnExists(f"{app_label}_pony", "id")
        # Change to a primary key.
        project_state = new_state
        new_state = new_state.clone()
        operation = migrations.AlterField(
            "Pony", "id", models.UUIDField(primary_key=True)
        )
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)