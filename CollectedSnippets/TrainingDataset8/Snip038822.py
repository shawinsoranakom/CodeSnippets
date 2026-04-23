def test_check_session_state_rules_no_val(
        self, patched_st_warning, patched_get_session_state
    ):
        mock_session_state = MagicMock()
        mock_session_state.is_new_state_value.return_value = True
        patched_get_session_state.return_value = mock_session_state

        check_session_state_rules(None, key="the key")

        patched_st_warning.assert_not_called()