def test_set_item(self):
        """`__setitem__` calls through to SessionState.
        If disconnected, it's a no-op.
        """
        # Not disconnected: update wrapped State
        safe_state, mock_state = _create_state_spy({}, disconnect=False)
        safe_state["baz"] = 123
        self.assertEqual(123, safe_state["baz"])
        self.assertEqual(123, mock_state["baz"])

        # Disconnected: no-op
        safe_state, mock_state = _create_state_spy({}, disconnect=True)
        safe_state["baz"] = 123
        self.assertRaises(KeyError, lambda: safe_state["baz"])
        self.assertRaises(KeyError, lambda: mock_state["baz"])