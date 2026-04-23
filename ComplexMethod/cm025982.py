async def _async_handle_discovered(self, hostname: str) -> ConfigFlowResult:
        entry: HeosConfigEntry | None = await self.async_set_unique_id(DOMAIN)
        # Abort early when discovery is ignored or host is part of the current system
        if entry and (
            entry.source == SOURCE_IGNORE or hostname in _get_current_hosts(entry)
        ):
            return self.async_abort(reason="single_instance_allowed")

        # Connect to discovered host and get system information
        heos = Heos(HeosOptions(hostname, events=False, heart_beat=False))
        try:
            await heos.connect()
            system_info = await heos.get_system_info()
        except HeosError as error:
            _LOGGER.debug(
                "Failed to retrieve system information from discovered HEOS device %s",
                hostname,
                exc_info=error,
            )
            return self.async_abort(reason="cannot_connect")
        finally:
            await heos.disconnect()

        # Select the preferred host, if available
        if system_info.preferred_hosts and system_info.preferred_hosts[0].ip_address:
            hostname = system_info.preferred_hosts[0].ip_address

        # Move to confirmation when not configured
        if entry is None:
            self._discovered_host = hostname
            return await self.async_step_confirm_discovery()

        # Only update if the configured host isn't part of the discovered hosts to ensure new players that come online don't trigger a reload
        if entry.data[CONF_HOST] not in [host.ip_address for host in system_info.hosts]:
            _LOGGER.debug(
                "Updated host %s to discovered host %s", entry.data[CONF_HOST], hostname
            )
            return self.async_update_reload_and_abort(
                entry,
                data_updates={CONF_HOST: hostname},
                reason="reconfigure_successful",
            )
        return self.async_abort(reason="single_instance_allowed")