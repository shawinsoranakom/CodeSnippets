def test_get_serialized_json_value(self):
        self.wstates.set_from_value("widget_id_3", {"foo": 5})
        self.wstates.set_widget_metadata(
            WidgetMetadata(
                id="widget_id_3",
                deserializer=lambda x, s: x,
                serializer=identity,
                value_type="json_value",
            )
        )

        serialized = self.wstates.get_serialized("widget_id_3")
        assert serialized.id == "widget_id_3"
        assert serialized.json_value == '{"foo": 5}'