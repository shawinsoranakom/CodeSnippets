def patch_execute_statements(self, execute_statements):
        return mock.patch.object(
            DatabaseCreation, "_execute_statements", execute_statements
        )