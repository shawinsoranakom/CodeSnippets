def test_rerun_with_stopped_scriptrunner(self, mock_create_scriptrunner: MagicMock):
        """If have a ScriptRunner but it's shutting down and cannot handle
        new rerun requests, we'll create a new ScriptRunner."""
        session = _create_test_session()

        mock_stopped_scriptrunner = MagicMock(spec=ScriptRunner)
        mock_stopped_scriptrunner.request_rerun = MagicMock(return_value=False)
        session._scriptrunner = mock_stopped_scriptrunner

        session.request_rerun(None)

        # The stopped ScriptRunner will reject the request...
        mock_stopped_scriptrunner.request_rerun.assert_called_once_with(RerunData())

        # So we'll create a new ScriptRunner.
        mock_create_scriptrunner.assert_called_once_with(RerunData())