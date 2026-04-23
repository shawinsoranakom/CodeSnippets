def test_get_nonexistent(self):
        session_state = SessionState()
        self.assertRaises(KeyError, lambda: session_state["fake_widget_id"])