def test_alter_field_with_func_unique_constraint(self):
        app_label = "test_alfuncuc"
        constraint_name = f"{app_label}_pony_uq"
        table_name = f"{app_label}_pony"
        project_state = self.set_up_test_model(
            app_label,
            constraints=[
                models.UniqueConstraint("pink", "weight", name=constraint_name)
            ],
        )
        operation = migrations.AlterField(
            "Pony", "pink", models.IntegerField(null=True)
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        if connection.features.supports_expression_indexes:
            self.assertIndexNameExists(table_name, constraint_name)
        with connection.schema_editor() as editor:
            operation.database_backwards(app_label, editor, new_state, project_state)
        if connection.features.supports_expression_indexes:
            self.assertIndexNameExists(table_name, constraint_name)