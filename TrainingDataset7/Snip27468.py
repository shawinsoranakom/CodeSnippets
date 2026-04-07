def test_indexes_ignore_swapped(self):
        """
        Add/RemoveIndex operations ignore swapped models.
        """
        operation = migrations.AddIndex(
            "Pony", models.Index(fields=["pink"], name="my_name_idx")
        )
        project_state, new_state = self.make_test_state("test_adinigsw", operation)
        with connection.schema_editor() as editor:
            # No database queries should be run for swapped models
            operation.database_forwards(
                "test_adinigsw", editor, project_state, new_state
            )
            operation.database_backwards(
                "test_adinigsw", editor, new_state, project_state
            )

        operation = migrations.RemoveIndex(
            "Pony", models.Index(fields=["pink"], name="my_name_idx")
        )
        project_state, new_state = self.make_test_state("test_rminigsw", operation)
        with connection.schema_editor() as editor:
            operation.database_forwards(
                "test_rminigsw", editor, project_state, new_state
            )
            operation.database_backwards(
                "test_rminigsw", editor, new_state, project_state
            )