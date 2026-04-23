def test_rerun_with_active_scriptrunner(self, mock_create_scriptrunner: MagicMock):
        """If we have an active ScriptRunner, it receives rerun requests."""
        session = _create_test_session()

        mock_active_scriptrunner = MagicMock(spec=ScriptRunner)
        mock_active_scriptrunner.request_rerun = MagicMock(return_value=True)
        session._scriptrunner = mock_active_scriptrunner

        session.request_rerun(None)

        # The active ScriptRunner will accept the rerun request...
        mock_active_scriptrunner.request_rerun.assert_called_once_with(RerunData())

        # So _create_scriptrunner should not be called.
        mock_create_scriptrunner.assert_not_called()