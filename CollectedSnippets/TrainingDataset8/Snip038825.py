def test_check_session_state_rules_writes_not_allowed(
        self, patched_get_session_state
    ):
        mock_session_state = MagicMock()
        mock_session_state.is_new_state_value.return_value = True
        patched_get_session_state.return_value = mock_session_state

        with pytest.raises(StreamlitAPIException) as e:
            check_session_state_rules(5, key="the key", writes_allowed=False)

        assert "cannot be set using st.session_state" in str(e.value)