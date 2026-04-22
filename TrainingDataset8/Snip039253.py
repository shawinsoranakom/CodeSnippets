def test_clear_cache_resets_session_state(self):
        session = _create_test_session()
        session._session_state["foo"] = "bar"
        session._handle_clear_cache_request()
        self.assertTrue("foo" not in session._session_state)