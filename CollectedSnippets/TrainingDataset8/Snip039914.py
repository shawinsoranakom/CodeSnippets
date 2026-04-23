def test_get_widget_states(self):
        """`get_widget_states` calls thru to SessionState, unless disconnected."""
        for disconnected in (False, True):
            with self.subTest(f"disconnected={disconnected}"):
                safe_state, mock_state = _create_state_spy({}, disconnected)
                mock_state.get_widget_states = MagicMock(return_value=[1, 2, 3])

                result = safe_state.get_widget_states()

                if disconnected:
                    mock_state.get_widget_states.assert_not_called()
                    self.assertEqual([], result)
                else:
                    mock_state.get_widget_states.assert_called_once_with()
                    self.assertEqual([1, 2, 3], result)