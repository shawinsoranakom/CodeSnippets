def filtered_state(self) -> Dict[str, Any]:
        """The combined session and widget state, excluding keyless widgets."""

        wid_key_map = self._reverse_key_wid_map

        state: Dict[str, Any] = {}

        # We can't write `for k, v in self.items()` here because doing so will
        # run into a `KeyError` if widget metadata has been cleared (which
        # happens when the streamlit server restarted or the cache was cleared),
        # then we receive a widget's state from a browser.
        for k in self._keys():
            if not _is_widget_id(k) and not _is_internal_key(k):
                state[k] = self[k]
            elif _is_keyed_widget_id(k):
                try:
                    key = wid_key_map[k]
                    state[key] = self[k]
                except KeyError:
                    # Widget id no longer maps to a key, it is a not yet
                    # cleared value in old state for a reset widget
                    pass

        return state