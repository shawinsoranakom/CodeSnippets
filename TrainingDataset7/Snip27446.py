def test_run_python_noop(self):
        """
        #24098 - Tests no-op RunPython operations.
        """
        project_state = ProjectState()
        new_state = project_state.clone()
        operation = migrations.RunPython(
            migrations.RunPython.noop, migrations.RunPython.noop
        )
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_runpython", editor, project_state, new_state
            )
            operation.database_backwards(
                "test_runpython", editor, new_state, project_state
            )