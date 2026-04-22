def test_is_new_state_value(self):
        """`is_new_state_value` calls thru to SessionState, unless disconnected."""
        for disconnected in (False, True):
            with self.subTest(f"disconnected={disconnected}"):
                safe_state, mock_state = _create_state_spy({}, disconnected)
                mock_state.is_new_state_value = MagicMock(return_value=True)

                result = safe_state.is_new_state_value("mock_user_key")

                if disconnected:
                    mock_state.is_new_state_value.assert_not_called()
                    self.assertEqual(False, result)
                else:
                    mock_state.is_new_state_value.assert_called_once_with(
                        "mock_user_key"
                    )
                    self.assertEqual(True, result)