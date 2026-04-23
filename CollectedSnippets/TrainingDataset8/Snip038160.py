def set_widgets_from_proto(self, widget_states: WidgetStatesProto) -> None:
        """Set the value of all widgets represented in the given WidgetStatesProto."""
        for state in widget_states.widgets:
            self._new_widget_state.set_widget_from_proto(state)