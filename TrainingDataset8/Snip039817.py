def test_rerun_while_stopped(self):
        """Requesting a rerun while STOPPED will return False."""
        reqs = ScriptRequests()
        reqs.request_stop()
        success = reqs.request_rerun(RerunData())
        self.assertFalse(success)
        self.assertEqual(ScriptRequestType.STOP, reqs._state)