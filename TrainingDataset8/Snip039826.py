def test_on_script_complete_with_no_request(self):
        """Return STOP; transition to the STOP state."""
        reqs = ScriptRequests()
        result = reqs.on_scriptrunner_ready()
        self.assertEqual(ScriptRequest(ScriptRequestType.STOP), result)
        self.assertEqual(ScriptRequestType.STOP, reqs._state)