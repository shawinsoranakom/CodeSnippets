def test_starts_running(self):
        """ScriptRequests starts in the CONTINUE state."""
        reqs = ScriptRequests()
        self.assertEqual(ScriptRequestType.CONTINUE, reqs._state)