async def _listen(self) -> None:
        """Listen to Syncthing events."""
        events = self._client.events
        server_was_unavailable = False
        while True:
            if await self._server_available():
                if server_was_unavailable:
                    _LOGGER.warning(
                        "The syncthing server '%s' is back online", self._client.url
                    )
                    async_dispatcher_send(
                        self._hass, f"{SERVER_AVAILABLE}-{self._server_id}"
                    )
                    server_was_unavailable = False
            else:
                await asyncio.sleep(RECONNECT_INTERVAL.total_seconds())
                continue
            try:
                async for event in events.listen():
                    if events.last_seen_id == 0:
                        continue  # skipping historical events from the first batch
                    if event["type"] not in EVENTS:
                        continue

                    signal_name = EVENTS[event["type"]]
                    folder = event["data"].get("folder") or event["data"]["id"]
                    async_dispatcher_send(
                        self._hass,
                        f"{signal_name}-{self._server_id}-{folder}",
                        event,
                    )
            except aiosyncthing.exceptions.SyncthingError:
                _LOGGER.warning(
                    (
                        "The syncthing server '%s' is not available. Sleeping %i"
                        " seconds and retrying"
                    ),
                    self._client.url,
                    RECONNECT_INTERVAL.total_seconds(),
                )
                async_dispatcher_send(
                    self._hass, f"{SERVER_UNAVAILABLE}-{self._server_id}"
                )
                await asyncio.sleep(RECONNECT_INTERVAL.total_seconds())
                server_was_unavailable = True
                continue