async def _async_from_discovery(
        self, host: str, friendly_name: str, discovered_macs: list[str]
    ) -> ConfigFlowResult:
        """Handle a discovered synology_dsm via zeroconf or ssdp."""
        existing_entry = None
        for discovered_mac in discovered_macs:
            await self.async_set_unique_id(discovered_mac)
            if existing_entry := self._async_get_existing_entry(discovered_mac):
                break
            self._abort_if_unique_id_configured()

        if (
            existing_entry
            and is_ip(existing_entry.data[CONF_HOST])
            and is_ip(host)
            and existing_entry.data[CONF_HOST] != host
            and ip(existing_entry.data[CONF_HOST]).version == ip(host).version
        ):
            _LOGGER.debug(
                "Update host from '%s' to '%s' for NAS '%s' via discovery",
                existing_entry.data[CONF_HOST],
                host,
                existing_entry.unique_id,
            )
            self.hass.config_entries.async_update_entry(
                existing_entry,
                data={**existing_entry.data, CONF_HOST: host},
            )
            return self.async_abort(reason="reconfigure_successful")

        if existing_entry:
            return self.async_abort(reason="already_configured")

        self.discovered_conf = {
            CONF_NAME: friendly_name,
            CONF_HOST: host,
        }
        self.context["title_placeholders"] = self.discovered_conf
        return await self.async_step_link()