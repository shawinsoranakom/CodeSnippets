def test_items(self):
        assert self.wstates.items() == {("widget_id_1", "5"), ("widget_id_2", 5)}