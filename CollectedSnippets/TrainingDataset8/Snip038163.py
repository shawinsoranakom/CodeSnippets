def _widget_changed(self, widget_id: str) -> bool:
        """True if the given widget's value changed between the previous
        script run and the current script run.
        """
        new_value = self._new_widget_state.get(widget_id)
        old_value = self._old_state.get(widget_id)
        changed: bool = new_value != old_value
        return changed