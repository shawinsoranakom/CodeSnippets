def test_run_sql_params_invalid(self):
        """
        #23426 - RunSQL should fail when a list of statements with an incorrect
        number of tuples is given.
        """
        project_state = self.set_up_test_model("test_runsql")
        new_state = project_state.clone()
        operation = migrations.RunSQL(
            # forwards
            [["INSERT INTO foo (bar) VALUES ('buz');"]],
            # backwards
            (("DELETE FROM foo WHERE bar = 'buz';", "invalid", "parameter count"),),
        )

        with connection.schema_editor() as editor:
            with self.assertRaisesMessage(ValueError, "Expected a 2-tuple but got 1"):
                operation.database_forwards(
                    "test_runsql", editor, project_state, new_state
                )

        with connection.schema_editor() as editor:
            with self.assertRaisesMessage(ValueError, "Expected a 2-tuple but got 3"):
                operation.database_backwards(
                    "test_runsql", editor, new_state, project_state
                )