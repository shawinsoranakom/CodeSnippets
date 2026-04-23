def test_rerun_with_no_scriptrunner(self, mock_create_scriptrunner: MagicMock):
        """If we don't have a ScriptRunner, a rerun request will result in
        one being created."""
        session = _create_test_session()
        session.request_rerun(None)
        mock_create_scriptrunner.assert_called_once_with(RerunData())