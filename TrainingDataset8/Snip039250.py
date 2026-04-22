def test_shutdown_with_running_scriptrunner(self):
        """If we have a running ScriptRunner, shutting down should stop it."""
        session = _create_test_session()
        mock_scriptrunner = MagicMock(spec=ScriptRunner)
        session._scriptrunner = mock_scriptrunner

        session.shutdown()
        mock_scriptrunner.request_stop.assert_called_once()

        mock_scriptrunner.reset_mock()

        # A 2nd shutdown call should have no affect.
        session.shutdown()
        mock_scriptrunner.request_stop.assert_not_called()