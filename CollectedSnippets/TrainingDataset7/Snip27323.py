def test_rename_model_no_relations_with_db_table_noop(self):
        app_label = "test_rmwdbtnoop"
        project_state = self.set_up_test_model(app_label, db_table="my_pony")
        operation = migrations.RenameModel("Pony", "LittleHorse")
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            operation.database_forwards(app_label, editor, project_state, new_state)