def on_script_will_rerun(self, latest_widget_states: WidgetStatesProto) -> None:
        """Called by ScriptRunner before its script re-runs.

        Update widget data and call callbacks on widgets whose value changed
        between the previous and current script runs.
        """
        # Update ourselves with the new widget_states. The old widget states,
        # used to skip callbacks if values haven't changed, are also preserved.
        self._compact_state()
        self.set_widgets_from_proto(latest_widget_states)
        self._call_callbacks()