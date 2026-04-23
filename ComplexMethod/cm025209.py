async def _writer(
        self,
        connection: ActiveConnection,
        send_bytes_text: Callable[[bytes], Coroutine[Any, Any, None]],
    ) -> None:
        """Write outgoing messages."""
        # Variables are set locally to avoid lookups in the loop
        message_queue = self._message_queue
        logger = self._logger
        wsock = self._wsock
        loop = self._loop
        debug = logger.debug
        can_coalesce = connection.can_coalesce
        ready_message_count = len(message_queue)
        # Exceptions if Socket disconnected or cancelled by connection handler
        try:
            while not wsock.closed:
                if not message_queue:
                    self._ready_future = loop.create_future()
                    ready_message_count = await self._ready_future

                if self._closing:
                    return

                if not can_coalesce:
                    # coalesce may be enabled later in the connection
                    can_coalesce = connection.can_coalesce

                if not can_coalesce or ready_message_count == 1:
                    message = message_queue.popleft()
                    if self._debug:
                        debug("%s: Sending %s", self.description, message)
                    await send_bytes_text(message)
                    continue

                coalesced_messages = b"".join((b"[", b",".join(message_queue), b"]"))
                message_queue.clear()
                if self._debug:
                    debug("%s: Sending %s", self.description, coalesced_messages)
                await send_bytes_text(coalesced_messages)
        except asyncio.CancelledError:
            debug("%s: Writer cancelled", self.description)
            raise
        except (RuntimeError, ConnectionResetError) as ex:
            debug("%s: Unexpected error in writer: %s", self.description, ex)
        finally:
            debug("%s: Writer done", self.description)
            # Clean up the peak checker when we shut down the writer
            self._cancel_peak_checker()