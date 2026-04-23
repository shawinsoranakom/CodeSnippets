def _cull_nonexistent(self, widget_ids: Set[str]) -> None:
        self._new_widget_state.cull_nonexistent(widget_ids)

        # Remove entries from _old_state corresponding to
        # widgets not in widget_ids.
        self._old_state = {
            k: v
            for k, v in self._old_state.items()
            if (k in widget_ids or not _is_widget_id(k))
        }