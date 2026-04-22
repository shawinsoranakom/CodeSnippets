def test_on_script_finished(self):
        """`on_script_finished` calls thru to SessionState, unless disconnected."""
        for disconnected in (False, True):
            with self.subTest(f"disconnected={disconnected}"):
                safe_state, mock_state = _create_state_spy({}, disconnected)

                widget_ids_this_run = {"foo", "bar"}
                safe_state.on_script_finished(widget_ids_this_run)

                if disconnected:
                    mock_state.on_script_finished.assert_not_called()
                else:
                    mock_state.on_script_finished.assert_called_once_with(
                        widget_ids_this_run
                    )