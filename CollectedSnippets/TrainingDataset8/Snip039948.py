def setUp(self):
        wstates = WStates()
        self.wstates = wstates

        widget_state = WidgetStateProto()
        widget_state.id = "widget_id_1"
        widget_state.int_value = 5
        wstates.set_widget_from_proto(widget_state)
        wstates.set_widget_metadata(
            WidgetMetadata(
                id="widget_id_1",
                deserializer=lambda x, s: str(x),
                serializer=lambda x: int(x),
                value_type="int_value",
            )
        )

        wstates.set_from_value("widget_id_2", 5)
        wstates.set_widget_metadata(
            WidgetMetadata(
                id="widget_id_2",
                deserializer=lambda x, s: x,
                serializer=identity,
                value_type="int_value",
            )
        )