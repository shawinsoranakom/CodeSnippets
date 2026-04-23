def test_get_from_json_value(self):
        widget_state = WidgetStateProto()
        widget_state.id = "widget_id_3"
        widget_state.json_value = '{"foo":5}'

        self.wstates.set_widget_from_proto(widget_state)
        self.wstates.set_widget_metadata(
            WidgetMetadata(
                id="widget_id_3",
                deserializer=lambda x, s: x,
                serializer=identity,
                value_type="json_value",
            )
        )

        assert self.wstates["widget_id_3"] == {"foo": 5}