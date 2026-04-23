def test_should_set_frontend_state_value_new_widget(self):
        # The widget is being registered for the first time, so there's no need
        # to have the frontend update with a new value.
        wstates = WStates()
        self.session_state._new_widget_state = wstates

        WIDGET_VALUE = 123

        metadata = WidgetMetadata(
            id=f"{GENERATED_WIDGET_KEY_PREFIX}-0-widget_id_1",
            deserializer=lambda _, __: WIDGET_VALUE,
            serializer=identity,
            value_type="int_value",
        )
        wsr = self.session_state.register_widget(
            metadata=metadata,
            user_key="widget_id_1",
        )
        assert not wsr.value_changed
        assert self.session_state["widget_id_1"] == WIDGET_VALUE