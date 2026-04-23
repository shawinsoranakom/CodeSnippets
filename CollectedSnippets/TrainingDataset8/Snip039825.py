def test_on_script_yield_with_rerun_request(self):
        """Return RERUN; transition to the CONTINUE state."""
        reqs = ScriptRequests()
        reqs.request_rerun(RerunData())

        result = reqs.on_scriptrunner_yield()
        self.assertEqual(ScriptRequest(ScriptRequestType.RERUN, RerunData()), result)
        self.assertEqual(ScriptRequestType.CONTINUE, reqs._state)