async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Handle DHCP discovery."""
        self.mac = format_mac(discovery_info.macaddress)
        self.host = discovery_info.ip
        if self.hass.config_entries.flow.async_has_matching_flow(self):
            return self.async_abort(reason="already_in_progress")

        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.data.get(CONF_MAC) == self.mac:
                result = self.hass.config_entries.async_update_entry(
                    entry,
                    data={
                        **entry.data,
                        CONF_HOST: discovery_info.ip,
                    },
                )
                if result:
                    self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
            if entry.data[CONF_HOST] == discovery_info.ip:
                if (
                    not entry.data.get(CONF_MAC)
                    and entry.state is ConfigEntryState.LOADED
                ):
                    result = self.hass.config_entries.async_update_entry(
                        entry,
                        data={
                            **entry.data,
                            CONF_MAC: self.mac,
                        },
                    )
                    if result:
                        self.hass.config_entries.async_schedule_reload(entry.entry_id)
                return self.async_abort(reason="already_configured")
        try:
            # Use load_selector = 0 to fetch the panel model without authentication.
            (model, _) = await try_connect(
                {CONF_HOST: discovery_info.ip, CONF_PORT: 7700}, 0
            )
        except (
            OSError,
            ConnectionRefusedError,
            ssl.SSLError,
            asyncio.exceptions.TimeoutError,
        ):
            return self.async_abort(reason="cannot_connect")
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return self.async_abort(reason="unknown")
        self.context["title_placeholders"] = {
            "model": model,
            "host": discovery_info.ip,
        }
        self._data = {
            CONF_HOST: discovery_info.ip,
            CONF_MAC: self.mac,
            CONF_MODEL: model,
            CONF_PORT: 7700,
        }

        return await self.async_step_auth()