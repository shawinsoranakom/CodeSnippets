def test_create_scriptrunner(self, mock_scriptrunner: MagicMock):
        """Test that _create_scriptrunner does what it should."""
        session = _create_test_session()
        self.assertIsNone(session._scriptrunner)

        session._create_scriptrunner(initial_rerun_data=RerunData())

        # Assert that the ScriptRunner constructor was called.
        mock_scriptrunner.assert_called_once_with(
            session_id=session.id,
            main_script_path=session._session_data.main_script_path,
            client_state=session._client_state,
            session_state=session._session_state,
            uploaded_file_mgr=session._uploaded_file_mgr,
            initial_rerun_data=RerunData(),
            user_info={"email": "test@test.com"},
        )

        self.assertIsNotNone(session._scriptrunner)

        # And that the ScriptRunner was initialized and started.
        scriptrunner: MagicMock = cast(MagicMock, session._scriptrunner)
        scriptrunner.on_event.connect.assert_called_once_with(
            session._on_scriptrunner_event
        )
        scriptrunner.start.assert_called_once()