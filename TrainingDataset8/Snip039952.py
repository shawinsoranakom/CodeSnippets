def test_getitem_serialized(self):
        assert isinstance(self.wstates.states["widget_id_1"], Serialized)
        assert self.wstates["widget_id_1"] == "5"
        assert self.wstates.states["widget_id_1"] == Value("5")