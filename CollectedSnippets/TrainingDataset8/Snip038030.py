def _enqueued_some_message(self) -> None:
        """Callback called by AppSession after the AppSession has enqueued a
        message. Sets the "needs_send_data" event, which causes our core
        loop to wake up and flush client message queues.

        Notes
        -----
        Threading: SAFE. May be called on any thread.
        """
        async_objs = self._get_async_objs()
        async_objs.eventloop.call_soon_threadsafe(async_objs.need_send_data.set)