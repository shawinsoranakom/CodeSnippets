def test_getitem_nonexistent(self):
        with pytest.raises(KeyError):
            self.wstates["nonexistent_widget_id"]