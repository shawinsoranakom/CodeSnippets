def test_check_session_state_rules_prints_warning(
        self, patched_st_warning, patched_get_session_state
    ):
        mock_session_state = MagicMock()
        mock_session_state.is_new_state_value.return_value = True
        patched_get_session_state.return_value = mock_session_state

        check_session_state_rules(5, key="the key")

        patched_st_warning.assert_called_once()
        args, kwargs = patched_st_warning.call_args
        warning_msg = args[0]
        assert 'The widget with key "the key"' in warning_msg