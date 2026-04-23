def stop(self) -> None:
        """Request that Streamlit close all sessions and stop running.
        Note that Streamlit won't stop running immediately.

        Notes
        -----
        Threading: SAFE. May be called from any thread.
        """

        async_objs = self._get_async_objs()

        def stop_on_eventloop():
            if self._state in (RuntimeState.STOPPING, RuntimeState.STOPPED):
                return

            LOGGER.debug("Runtime stopping...")
            self._set_state(RuntimeState.STOPPING)
            async_objs.must_stop.set()

        async_objs.eventloop.call_soon_threadsafe(stop_on_eventloop)