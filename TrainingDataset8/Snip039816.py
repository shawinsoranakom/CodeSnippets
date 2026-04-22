def test_stop(self):
        """A stop request will unconditionally succeed regardless of the
        ScriptRequests' current state.
        """

        for state in ScriptRequestType:
            reqs = ScriptRequests()
            reqs._state = state
            reqs.request_stop()
            self.assertEqual(ScriptRequestType.STOP, reqs._state)