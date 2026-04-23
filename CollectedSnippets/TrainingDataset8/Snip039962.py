def test_get_serialized_already_serialized(self):
        serialized = self.wstates.get_serialized("widget_id_2")
        assert serialized.id == "widget_id_2"
        assert serialized.int_value == 5