def test_get_serialized(self):
        serialized = self.wstates.get_serialized("widget_id_1")
        assert serialized.id == "widget_id_1"
        assert serialized.int_value == 5