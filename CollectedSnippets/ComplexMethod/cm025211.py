async def async_handle(self) -> web.WebSocketResponse:
        """Handle a websocket response."""
        request = self._request
        wsock = self._wsock
        logger = self._logger
        hass = self._hass

        try:
            async with asyncio.timeout(10):
                await wsock.prepare(request)
        except ConnectionResetError:
            # Likely the client disconnected before we prepared the websocket
            logger.debug(
                "%s: Connection reset by peer while preparing WebSocket",
                self.description,
            )
            return wsock
        except TimeoutError:
            logger.warning("Timeout preparing request from %s", request.remote)
            return wsock

        logger.debug("%s: Connected from %s", self.description, request.remote)
        self._handle_task = asyncio.current_task()

        unsub_stop = hass.bus.async_listen(
            EVENT_HOMEASSISTANT_STOP, self._async_handle_hass_stop
        )
        cancel_logging_listener = hass.bus.async_listen(
            EVENT_LOGGING_CHANGED, self._async_logging_changed
        )

        writer = wsock._writer  # noqa: SLF001
        if TYPE_CHECKING:
            assert writer is not None

        send_bytes_text = partial(writer.send_frame, opcode=WSMsgType.TEXT)
        auth = AuthPhase(
            logger, hass, self._send_message, self._cancel, request, send_bytes_text
        )
        connection: ActiveConnection | None = None
        disconnect_warn: str | None = None

        try:
            connection = await self._async_handle_auth_phase(auth, send_bytes_text)
            self._async_increase_writer_limit(writer)
            await self._async_websocket_command_phase(connection)
        except asyncio.CancelledError:
            logger.debug("%s: Connection cancelled", self.description)
            raise
        except Disconnect as ex:
            if disconnect_msg := str(ex):
                disconnect_warn = disconnect_msg

            logger.debug("%s: Connection closed by client: %s", self.description, ex)
        except Exception:
            logger.exception(
                "%s: Unexpected error inside websocket API", self.description
            )
        finally:
            cancel_logging_listener()
            unsub_stop()

            self._cancel_peak_checker()

            if connection is not None:
                connection.async_handle_close()

            self._closing = True
            if self._ready_future and not self._ready_future.done():
                self._ready_future.set_result(len(self._message_queue))

            await self._async_cleanup_writer_and_close(disconnect_warn, connection)

        return wsock