def test_del_item(self):
        """`__delitem__` calls through to SessionState.__getitem__.
        If disconnected, it always raises a KeyError.
        """
        # Not disconnected: update wrapped State
        safe_state, mock_state = _create_state_spy({"foo": "bar"}, disconnect=False)
        del safe_state["foo"]
        self.assertRaises(KeyError, lambda: safe_state["foo"])
        self.assertRaises(KeyError, lambda: mock_state["foo"])

        with self.assertRaises(KeyError):
            # (Weird Python rule: `del` is not an expression, so it can't be
            # in the body of a lambda.)
            del safe_state["not_a_key"]

        # Disconnected: raise a KeyError for all keys
        safe_state, _ = _create_state_spy({"foo": "bar"}, disconnect=True)
        with self.assertRaises(KeyError):
            del safe_state["foo"]