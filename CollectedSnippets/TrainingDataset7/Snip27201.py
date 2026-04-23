def test_unrelated_applied_migrations_mutate_state(self):
        """
        #26647 - Unrelated applied migrations should be part of the final
        state in both directions.
        """
        executor = MigrationExecutor(connection)
        executor.migrate(
            [
                ("mutate_state_b", "0002_add_field"),
            ]
        )
        # Migrate forward.
        executor.loader.build_graph()
        state = executor.migrate(
            [
                ("mutate_state_a", "0001_initial"),
            ]
        )
        self.assertIn("added", state.models["mutate_state_b", "b"].fields)
        executor.loader.build_graph()
        # Migrate backward.
        state = executor.migrate(
            [
                ("mutate_state_a", None),
            ]
        )
        self.assertIn("added", state.models["mutate_state_b", "b"].fields)
        executor.migrate(
            [
                ("mutate_state_b", None),
            ]
        )