def test_widget_changed(self):
        assert self.session_state._widget_changed("foo")
        self.session_state._new_widget_state.set_from_value("foo", "bar")
        assert not self.session_state._widget_changed("foo")