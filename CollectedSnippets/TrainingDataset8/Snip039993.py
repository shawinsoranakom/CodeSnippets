def test_getitem_error(self):
        with pytest.raises(KeyError):
            self.session_state["nonexistent"]