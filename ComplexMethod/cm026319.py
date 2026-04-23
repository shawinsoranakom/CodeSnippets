async def async_discover_client(self):
        """Handle Discovery step."""
        self.create_client()

        if TYPE_CHECKING:
            assert self.client is not None

        if self.device_config.get(CONF_ID):
            return

        try:
            details = await async_discover_netcast_details(self.hass, self.client)
        except LGNetCastDetailDiscoveryError as err:
            raise AbortFlow("cannot_connect") from err

        if (unique_id := details["uuid"]) is None:
            raise AbortFlow("invalid_host")

        self.device_config[CONF_ID] = unique_id
        self.device_config[CONF_MODEL] = details["model_name"]

        if CONF_NAME not in self.device_config:
            self.device_config[CONF_NAME] = details["friendly_name"] or DEFAULT_NAME