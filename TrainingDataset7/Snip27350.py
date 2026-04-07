def test_remove_fk(self):
        """
        Tests the RemoveField operation on a foreign key.
        """
        project_state = self.set_up_test_model("test_rfk", related_model=True)
        self.assertColumnExists("test_rfk_rider", "pony_id")
        operation = migrations.RemoveField("Rider", "pony")

        new_state = project_state.clone()
        operation.state_forwards("test_rfk", new_state)
        with connection.schema_editor() as editor:
            operation.database_forwards("test_rfk", editor, project_state, new_state)
        self.assertColumnNotExists("test_rfk_rider", "pony_id")
        with connection.schema_editor() as editor:
            operation.database_backwards("test_rfk", editor, new_state, project_state)
        self.assertColumnExists("test_rfk_rider", "pony_id")