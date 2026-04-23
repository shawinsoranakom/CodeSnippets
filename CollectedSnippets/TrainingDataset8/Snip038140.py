def set_widget_from_proto(self, widget_state: WidgetStateProto) -> None:
        """Set a widget's serialized value, overwriting any existing value it has."""
        self[widget_state.id] = Serialized(widget_state)