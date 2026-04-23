async def _listen(self) -> None:
        server_was_unavailable = False
        while True:
            try:
                async for event in self._client.events():
                    _LOGGER.debug("Received event: %s", event)
                    if server_was_unavailable:
                        _LOGGER.debug("Tractive is back online")
                        server_was_unavailable = False
                    if event["message"] == "health_overview":
                        self.send_health_overview_update(event)
                        continue
                    if (
                        "hardware" in event
                        and self._last_hw_time != event["hardware"]["time"]
                    ):
                        self._last_hw_time = event["hardware"]["time"]
                        self._send_hardware_update(event)
                        self._send_switch_update(event)
                    if (
                        "position" in event
                        and self._last_pos_time != event["position"]["time"]
                    ):
                        self._last_pos_time = event["position"]["time"]
                        self._send_position_update(event)
                    # If any key belonging to the switch is present in the event,
                    # we send a switch status update
                    if bool(set(SWITCH_KEY_MAP.values()).intersection(event)):
                        self._send_switch_update(event)
            except aiotractive.exceptions.UnauthorizedError:
                self._config_entry.async_start_reauth(self._hass)
                await self.unsubscribe()
                _LOGGER.error(
                    "Authentication failed for %s, try reconfiguring device",
                    self._config_entry.data[CONF_EMAIL],
                )
                return
            except (KeyError, TypeError) as error:
                _LOGGER.error("Error while listening for events: %s", error)
                continue
            except aiotractive.exceptions.TractiveError:
                _LOGGER.debug(
                    (
                        "Tractive is not available. Internet connection is down?"
                        " Sleeping %i seconds and retrying"
                    ),
                    RECONNECT_INTERVAL.total_seconds(),
                )
                self._last_hw_time = 0
                self._last_pos_time = 0
                async_dispatcher_send(
                    self._hass, f"{SERVER_UNAVAILABLE}-{self._user_id}"
                )
                await asyncio.sleep(RECONNECT_INTERVAL.total_seconds())
                server_was_unavailable = True
                continue