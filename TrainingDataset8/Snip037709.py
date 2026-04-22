def _enqueue_forward_msg(self, msg: ForwardMsg) -> None:
        """Enqueue a new ForwardMsg to our browser queue.

        This can be called on both the main thread and a ScriptRunner
        run thread.

        Parameters
        ----------
        msg : ForwardMsg
            The message to enqueue

        """
        if not config.get_option("client.displayEnabled"):
            return

        if self._debug_last_backmsg_id:
            msg.debug_last_backmsg_id = self._debug_last_backmsg_id

        self._session_data.enqueue(msg)
        if self._message_enqueued_callback:
            self._message_enqueued_callback()