def test_on_script_yield_with_stop_request(self):
        """Return STOP; remain in the STOP state."""
        reqs = ScriptRequests()
        reqs.request_stop()

        result = reqs.on_scriptrunner_yield()
        self.assertEqual(ScriptRequest(ScriptRequestType.STOP), result)
        self.assertEqual(ScriptRequestType.STOP, reqs._state)