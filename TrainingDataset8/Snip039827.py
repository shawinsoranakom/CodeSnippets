def test_on_script_complete_with_pending_request(self):
        """Return RERUN; transition to the CONTINUE state."""
        reqs = ScriptRequests()
        reqs.request_rerun(RerunData())

        result = reqs.on_scriptrunner_ready()
        self.assertEqual(ScriptRequest(ScriptRequestType.RERUN, RerunData()), result)
        self.assertEqual(ScriptRequestType.CONTINUE, reqs._state)