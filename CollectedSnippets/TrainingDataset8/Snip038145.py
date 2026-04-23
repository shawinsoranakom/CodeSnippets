def as_widget_states(self) -> List[WidgetStateProto]:
        """Return a list of serialized widget values for each widget with a value."""
        states = [
            self.get_serialized(widget_id)
            for widget_id in self.states.keys()
            if self.get_serialized(widget_id)
        ]
        states = cast(List[WidgetStateProto], states)
        return states