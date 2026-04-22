def test_on_script_yield_with_no_request(self):
        """Return None; remain in the CONTINUE state."""
        reqs = ScriptRequests()
        result = reqs.on_scriptrunner_yield()
        self.assertEqual(None, result)
        self.assertEqual(ScriptRequestType.CONTINUE, reqs._state)