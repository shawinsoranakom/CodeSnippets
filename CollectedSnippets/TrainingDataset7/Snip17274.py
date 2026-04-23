def test_ready(self):
        """
        Tests the ready property of the main registry.
        """
        # The main app registry is always ready when the tests run.
        self.assertIs(apps.ready, True)
        # Non-main app registries are populated in __init__.
        self.assertIs(Apps().ready, True)
        # The condition is set when apps are ready
        self.assertIs(apps.ready_event.is_set(), True)
        self.assertIs(Apps().ready_event.is_set(), True)