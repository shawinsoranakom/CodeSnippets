def test_shutdown(self, patched_disconnect):
        """Test that AppSession.shutdown behaves sanely."""
        session = _create_test_session()

        mock_file_mgr = MagicMock(spec=UploadedFileManager)
        session._uploaded_file_mgr = mock_file_mgr

        session.shutdown()
        self.assertEqual(AppSessionState.SHUTDOWN_REQUESTED, session._state)
        mock_file_mgr.remove_session_files.assert_called_once_with(session.id)
        patched_disconnect.assert_called_once_with(session._on_secrets_file_changed)

        # A 2nd shutdown call should have no effect.
        session.shutdown()
        self.assertEqual(AppSessionState.SHUTDOWN_REQUESTED, session._state)
        mock_file_mgr.remove_session_files.assert_called_once_with(session.id)