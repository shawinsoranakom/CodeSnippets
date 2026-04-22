def test_on_script_will_rerun(self):
        """`on_script_will_rerun` calls thru to SessionState, unless disconnected."""
        for disconnected in (False, True):
            with self.subTest(f"disconnected={disconnected}"):
                safe_state, mock_state = _create_state_spy({}, disconnected)

                latest_widget_states = MagicMock()
                safe_state.on_script_will_rerun(latest_widget_states)

                if disconnected:
                    mock_state.on_script_will_rerun.assert_not_called()
                else:
                    mock_state.on_script_will_rerun.assert_called_once_with(
                        latest_widget_states
                    )