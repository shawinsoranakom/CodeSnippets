def test_register_widget(self):
        """`register_widget` calls thru to SessionState, unless disconnected."""
        for disconnected in (False, True):
            with self.subTest(f"disconnected={disconnected}"):
                safe_state, mock_state = _create_state_spy({}, disconnected)

                widget_metadata = MagicMock()
                safe_state.register_widget(widget_metadata, "mock_user_key")

                if disconnected:
                    mock_state.register_widget.assert_not_called()
                else:
                    mock_state.register_widget.assert_called_once_with(
                        widget_metadata, "mock_user_key"
                    )