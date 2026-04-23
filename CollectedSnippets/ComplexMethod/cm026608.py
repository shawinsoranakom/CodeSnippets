async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a discovered konnected panel.

        This flow is triggered by the SSDP component. It will check if the
        device is already configured and attempt to finish the config if not.
        """
        _LOGGER.debug(discovery_info)

        try:
            if discovery_info.upnp[ATTR_UPNP_MANUFACTURER] != KONN_MANUFACTURER:
                return self.async_abort(reason="not_konn_panel")

            if not any(
                name in discovery_info.upnp[ATTR_UPNP_MODEL_NAME]
                for name in KONN_PANEL_MODEL_NAMES
            ):
                _LOGGER.warning(
                    "Discovered unrecognized Konnected device %s",
                    discovery_info.upnp.get(ATTR_UPNP_MODEL_NAME, "Unknown"),
                )
                return self.async_abort(reason="not_konn_panel")

        # If MAC is missing it is a bug in the device fw but we'll guard
        # against it since the field is so vital
        except KeyError:
            _LOGGER.error("Malformed Konnected SSDP info")
        else:
            # extract host/port from ssdp_location
            assert discovery_info.ssdp_location
            netloc = urlparse(discovery_info.ssdp_location).netloc.split(":")
            self._async_abort_entries_match(
                {CONF_HOST: netloc[0], CONF_PORT: int(netloc[1])}
            )

            try:
                status = await get_status(self.hass, netloc[0], int(netloc[1]))
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")

            self.data[CONF_HOST] = netloc[0]
            self.data[CONF_PORT] = int(netloc[1])
            self.data[CONF_ID] = status.get("chipId", status["mac"].replace(":", ""))
            self.data[CONF_MODEL] = status.get("model", KONN_MODEL)

            KonnectedFlowHandler.DISCOVERED_HOSTS[self.data[CONF_ID]] = {
                CONF_HOST: self.data[CONF_HOST],
                CONF_PORT: self.data[CONF_PORT],
            }
            return await self.async_step_confirm()

        return self.async_abort(reason="unknown")