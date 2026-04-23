def _call_callbacks(self) -> None:
        """Call any callback associated with each widget whose value
        changed between the previous and current script runs.
        """
        from streamlit.runtime.scriptrunner import RerunException

        changed_widget_ids = [
            wid for wid in self._new_widget_state if self._widget_changed(wid)
        ]
        for wid in changed_widget_ids:
            try:
                self._new_widget_state.call_callback(wid)
            except RerunException:
                st.warning(
                    "Calling st.experimental_rerun() within a callback is a no-op."
                )