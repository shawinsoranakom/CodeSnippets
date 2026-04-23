async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Initialize flow from ssdp."""
        updated_data: dict[str, str | int | bool] = {}

        device_url = urlparse(discovery_info.ssdp_location)
        if hostname := device_url.hostname:
            hostname = cast(str, hostname)
            updated_data[CONF_HOST] = hostname

        if not is_ipv4_address(str(hostname)):
            return self.async_abort(reason="not_ipv4_address")

        _LOGGER.debug("Netgear ssdp discovery info: %s", discovery_info)

        if ATTR_UPNP_SERIAL not in discovery_info.upnp:
            return self.async_abort(reason="no_serial")

        await self.async_set_unique_id(discovery_info.upnp[ATTR_UPNP_SERIAL])
        self._abort_if_unique_id_configured(updates=updated_data)

        if device_url.scheme == "https":
            updated_data[CONF_SSL] = True
        else:
            updated_data[CONF_SSL] = False

        updated_data[CONF_PORT] = DEFAULT_PORT
        for model in MODELS_PORT_80:
            if discovery_info.upnp.get(ATTR_UPNP_MODEL_NUMBER, "").startswith(
                model
            ) or discovery_info.upnp.get(ATTR_UPNP_MODEL_NAME, "").startswith(model):
                updated_data[CONF_PORT] = PORT_80
        for model in MODELS_PORT_5555:
            if discovery_info.upnp.get(ATTR_UPNP_MODEL_NUMBER, "").startswith(
                model
            ) or discovery_info.upnp.get(ATTR_UPNP_MODEL_NAME, "").startswith(model):
                updated_data[CONF_PORT] = PORT_5555
                updated_data[CONF_SSL] = True

        self.placeholders.update(updated_data)
        self.discovered = True

        return await self.async_step_user()