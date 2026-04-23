def test_rename_model_with_db_table_and_fk_noop(self):
        app_label = "test_rmwdbtfk"
        project_state = self.set_up_test_model(
            app_label, db_table="my_pony", related_model=True
        )
        new_state = project_state.clone()
        operation = migrations.RenameModel("Pony", "LittleHorse")
        operation.state_forwards(app_label, new_state)
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            operation.database_forwards(app_label, editor, project_state, new_state)