async def async_poll_manual_hosts(
        self, now: datetime.datetime | None = None
    ) -> None:
        """Add and maintain Sonos devices from a manual configuration."""

        # Loop through each configured host and verify that Soco attributes are available for it.
        for host in self.hosts.copy():
            ip_addr = await self.hass.async_add_executor_job(socket.gethostbyname, host)
            soco = SoCo(ip_addr)
            try:
                visible_zones = await self.hass.async_add_executor_job(
                    sync_get_visible_zones,
                    soco,
                )
            except HTTPError as err:
                await self._process_http_connection_error(err, ip_addr)
                continue
            except (
                OSError,
                SoCoException,
                Timeout,
                TimeoutError,
            ) as ex:
                if not self.hosts_in_error.get(ip_addr):
                    _LOGGER.warning(
                        "Could not get visible Sonos devices from %s: %s", ip_addr, ex
                    )
                    self.hosts_in_error[ip_addr] = True
                else:
                    _LOGGER.debug(
                        "Could not get visible Sonos devices from %s: %s", ip_addr, ex
                    )
                continue

            if self.hosts_in_error.pop(ip_addr, None):
                _LOGGER.warning("Connection reestablished to Sonos device %s", ip_addr)
            # Each speaker has the topology for other online speakers, so add them in here if they were not
            # configured. The metadata is already in Soco for these.
            if new_hosts := {
                x.ip_address for x in visible_zones if x.ip_address not in self.hosts
            }:
                _LOGGER.debug("Adding to manual hosts: %s", new_hosts)
                self.hosts.update(new_hosts)

            if self.is_device_invisible(ip_addr):
                _LOGGER.debug("Discarding %s from manual hosts", ip_addr)
                self.hosts.discard(ip_addr)

        # Loop through each configured host that is not in error.  Send a discovery message
        # if a speaker does not already exist, or ping the speaker if it is unavailable.
        for host in self.hosts.copy():
            ip_addr = await self.hass.async_add_executor_job(socket.gethostbyname, host)
            soco = SoCo(ip_addr)
            # Skip hosts that are in error to avoid blocking call on soco.uuid in event loop
            if self.hosts_in_error.get(ip_addr):
                continue
            known_speaker = next(
                (
                    speaker
                    for speaker in self.data.discovered.values()
                    if speaker.soco.ip_address == ip_addr
                ),
                None,
            )
            if not known_speaker:
                try:
                    await self._async_handle_discovery_message(
                        soco.uid,
                        ip_addr,
                        "manual zone scan",
                    )
                except (
                    OSError,
                    SoCoException,
                    Timeout,
                    TimeoutError,
                ) as ex:
                    _LOGGER.warning("Discovery message failed to %s : %s", ip_addr, ex)
            elif not known_speaker.available:
                try:
                    await self.hass.async_add_executor_job(known_speaker.ping)
                    # Only send the message if the ping was successful.
                    async_dispatcher_send(
                        self.hass,
                        f"{SONOS_SPEAKER_ACTIVITY}-{soco.uid}",
                        "manual zone scan",
                    )
                except SonosUpdateError:
                    _LOGGER.debug(
                        "Manual poll to %s failed, keeping unavailable", ip_addr
                    )

        self.data.hosts_heartbeat = async_call_later(
            self.hass, DISCOVERY_INTERVAL.total_seconds(), self.async_poll_manual_hosts
        )