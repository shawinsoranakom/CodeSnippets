def test_filtered_state(self):
        """`filtered_state` calls thru to SessionState, unless disconnected."""
        for disconnected in (False, True):
            with self.subTest(f"disconnected={disconnected}"):
                safe_state, mock_state = _create_state_spy({}, disconnected)

                filtered_state_mock = PropertyMock(return_value={"foo": 10, "bar": 20})
                type(mock_state).filtered_state = filtered_state_mock

                result = safe_state.filtered_state
                if disconnected:
                    filtered_state_mock.assert_not_called()
                    self.assertEqual({}, result)
                else:
                    filtered_state_mock.assert_called_once()
                    self.assertEqual({"foo": 10, "bar": 20}, result)