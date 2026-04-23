async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by SSDP discovery."""
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("async_step_ssdp: discovery_info %s", pformat(discovery_info))

        await self._async_parse_discovery(discovery_info)
        if TYPE_CHECKING:
            # _async_parse_discovery unconditionally sets self._name
            assert self._name is not None

        # Abort if the device doesn't support all services required for a DmsDevice.
        # Use the discovery_info instead of DmsDevice.is_profile_device to avoid
        # contacting the device again.
        discovery_service_list = discovery_info.upnp.get(ATTR_UPNP_SERVICE_LIST)
        if not discovery_service_list:
            return self.async_abort(reason="not_dms")

        services = discovery_service_list.get("service")
        if not services:
            discovery_service_ids: set[str] = set()
        elif isinstance(services, list):
            discovery_service_ids = {service.get("serviceId") for service in services}
        else:
            # Only one service defined (etree_to_dict failed to make a list)
            discovery_service_ids = {services.get("serviceId")}

        if not DmsDevice.SERVICE_IDS.issubset(discovery_service_ids):
            return self.async_abort(reason="not_dms")

        # Abort if another config entry has the same location, in case the
        # device doesn't have a static and unique UDN (breaking the UPnP spec).
        self._async_abort_entries_match({CONF_URL: self._location})

        self.context["title_placeholders"] = {"name": self._name}

        return await self.async_step_confirm()