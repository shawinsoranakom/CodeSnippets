def test_rerun_while_running(self):
        """Requesting a rerun while in CONTINUE state will always succeed."""
        reqs = ScriptRequests()
        rerun_data = RerunData(query_string="test_query_string")
        success = reqs.request_rerun(rerun_data)
        self.assertTrue(success)
        self.assertEqual(ScriptRequestType.RERUN, reqs._state)
        self.assertEqual(rerun_data, reqs._rerun_data)