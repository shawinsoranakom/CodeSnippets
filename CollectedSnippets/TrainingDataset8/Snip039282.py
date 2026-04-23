def test_returns_true_if_changed_file_is_not_page(self):
        session = _create_test_session()
        session._client_state.page_script_hash = "hash1"

        self.assertEqual(
            session._should_rerun_on_file_change("some_other_file.py"), True
        )