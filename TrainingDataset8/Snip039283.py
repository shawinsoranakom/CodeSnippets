def test_returns_false_if_different_page_changed(self):
        session = _create_test_session()
        session._client_state.page_script_hash = "hash2"

        self.assertEqual(session._should_rerun_on_file_change("page1.py"), False)