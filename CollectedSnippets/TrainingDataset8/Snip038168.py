def get_widget_states(self) -> List[WidgetStateProto]:
        """Return a list of serialized widget values for each widget with a value."""
        return self._new_widget_state.as_widget_states()