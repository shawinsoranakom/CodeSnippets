def test_request_rerun_on_secrets_file_change(self, patched_connect):
        """AppSession should add a secrets listener on creation."""
        session = _create_test_session()
        patched_connect.assert_called_once_with(session._on_secrets_file_changed)