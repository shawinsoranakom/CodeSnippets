def test_fast_rerun(self, mock_create_scriptrunner: MagicMock):
        """If runner.fastReruns is enabled, a rerun request will stop the
        existing ScriptRunner and immediately create a new one.
        """
        session = _create_test_session()

        mock_active_scriptrunner = MagicMock(spec=ScriptRunner)
        session._scriptrunner = mock_active_scriptrunner

        session.request_rerun(None)

        # The active ScriptRunner should be shut down.
        mock_active_scriptrunner.request_rerun.assert_not_called()
        mock_active_scriptrunner.request_stop.assert_called_once()

        # And a new ScriptRunner should be created.
        mock_create_scriptrunner.assert_called_once()