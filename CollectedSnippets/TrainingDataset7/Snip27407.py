def test_alter_index_together_remove_with_unique_together(self):
        app_label = "test_alintoremove_wunto"
        table_name = "%s_pony" % app_label
        project_state = self.set_up_test_model(app_label, unique_together=True)
        self.assertUniqueConstraintExists(table_name, ["pink", "weight"])
        # Add index together.
        new_state = project_state.clone()
        operation = migrations.AlterIndexTogether("Pony", [("pink", "weight")])
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexExists(table_name, ["pink", "weight"])
        # Remove index together.
        project_state = new_state
        new_state = project_state.clone()
        operation = migrations.AlterIndexTogether("Pony", set())
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIndexNotExists(table_name, ["pink", "weight"])
        self.assertUniqueConstraintExists(table_name, ["pink", "weight"])