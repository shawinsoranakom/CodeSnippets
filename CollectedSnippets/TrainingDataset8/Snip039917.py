def test_get_item(self):
        """`__getitem__` calls through to SessionState.
        If disconnected, it always raises a KeyError.
        """
        # Not disconnected: return values from the wrapped SessionState
        safe_state, _ = _create_state_spy({"foo": "bar"}, disconnect=False)
        self.assertEqual("bar", safe_state["foo"])
        self.assertRaises(KeyError, lambda: safe_state["baz"])

        # Disconnected: raise a KeyError for all keys
        safe_state, _ = _create_state_spy({"foo": "bar"}, disconnect=True)
        self.assertRaises(KeyError, lambda: safe_state["foo"])