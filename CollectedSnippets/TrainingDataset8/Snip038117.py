def on_script_will_rerun(self, latest_widget_states: WidgetStatesProto) -> None:
        with self._lock:
            if self._disconnected:
                return

            # TODO: rewrite this to copy the callbacks list into a local
            #  variable so that we don't need to hold our lock for the
            #  duration. (This will also allow us to downgrade our RLock
            #  to a Lock.)
            self._state.on_script_will_rerun(latest_widget_states)