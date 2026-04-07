def _close_connections(self):
        # Used for mocking in tests.
        connections.close_all()