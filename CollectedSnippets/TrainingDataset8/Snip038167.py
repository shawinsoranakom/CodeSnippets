def _set_widget_metadata(self, widget_metadata: WidgetMetadata[Any]) -> None:
        """Set a widget's metadata."""
        widget_id = widget_metadata.id
        self._new_widget_state.widget_metadata[widget_id] = widget_metadata