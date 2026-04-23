def test_get_prev_widget_value_nonexistent(self):
        session_state = SessionState()
        self.assertRaises(KeyError, lambda: session_state["fake_widget_id"])