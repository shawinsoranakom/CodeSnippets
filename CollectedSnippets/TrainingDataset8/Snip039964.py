def test_get_serialized_array_value(self):
        widget_state = WidgetStateProto()
        widget_state.id = "widget_id_1"
        widget_state.int_array_value.data.extend([1, 2, 3, 4])
        self.wstates.set_widget_from_proto(widget_state)
        self.wstates.set_widget_metadata(
            WidgetMetadata(
                id="widget_id_1",
                deserializer=lambda x, s: x,
                serializer=identity,
                value_type="int_array_value",
            )
        )

        serialized = self.wstates.get_serialized("widget_id_1")
        assert serialized.id == "widget_id_1"
        assert list(serialized.int_array_value.data) == [1, 2, 3, 4]