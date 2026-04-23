def stop_on_eventloop():
            if self._state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
                return

            LOGGER.debug("Runtime stopping...")
            self._set_state(RuntimeState.STOPPING)
            async_objs.must_stop.set()