def _send_message(self, message: str | bytes | dict[str, Any]) -> None:
        """Queue sending a message to the client.

        Closes connection if the client is not reading the messages.

        Async friendly.
        """
        if self._closing:
            # Connection is cancelled, don't flood logs about exceeding
            # max pending messages.
            return

        if type(message) is not bytes:
            if isinstance(message, dict):
                message = message_to_json_bytes(message)
            elif isinstance(message, str):
                message = message.encode("utf-8")

        message_queue = self._message_queue
        message_queue.append(message)
        if (queue_size_after_add := len(message_queue)) >= MAX_PENDING_MSG:
            self._logger.error(
                (
                    "%s: Client unable to keep up with pending messages. Reached %s pending"
                    " messages. The system's load is too high or an integration is"
                    " misbehaving; Last message was: %s"
                ),
                self.description,
                MAX_PENDING_MSG,
                message,
            )
            self._cancel()
            return

        if self._release_ready_queue_size == 0:
            # Try to coalesce more messages to reduce the number of writes
            self._release_ready_queue_size = queue_size_after_add
            self._loop.call_soon(self._release_ready_future_or_reschedule)

        peak_checker_active = self._peak_checker_unsub is not None

        if queue_size_after_add <= PENDING_MSG_PEAK:
            if peak_checker_active:
                self._cancel_peak_checker()
            return

        if not peak_checker_active:
            self._peak_checker_unsub = async_call_later(
                self._hass, PENDING_MSG_PEAK_TIME, self._check_write_peak
            )