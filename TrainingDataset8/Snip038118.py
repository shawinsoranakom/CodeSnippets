def on_script_finished(self, widget_ids_this_run: Set[str]) -> None:
        with self._lock:
            if self._disconnected:
                return

            self._state.on_script_finished(widget_ids_this_run)