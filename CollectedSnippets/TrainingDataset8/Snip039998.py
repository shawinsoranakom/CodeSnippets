def test_delitem_errors(self):
        for key in ["_new_session_state", "_new_widget_state", "_old_state"]:
            with pytest.raises(KeyError):
                del self.session_state[key]

        with pytest.raises(KeyError):
            del self.session_state["nonexistent"]