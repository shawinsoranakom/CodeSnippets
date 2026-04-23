async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by SSDP discovery."""
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug("async_step_ssdp: discovery_info %s", pformat(discovery_info))

        await self._async_set_info_from_discovery(discovery_info)
        if TYPE_CHECKING:
            # _async_set_info_from_discovery unconditionally sets self._name
            assert self._name is not None

        if _is_ignored_device(discovery_info):
            return self.async_abort(reason="alternative_integration")

        # Abort if the device doesn't support all services required for a DmrDevice.
        if not _is_dmr_device(discovery_info):
            return self.async_abort(reason="not_dmr")

        # Abort if another config entry has the same location or MAC address, in
        # case the device doesn't have a static and unique UDN (breaking the
        # UPnP spec).
        for entry in self._async_current_entries(include_ignore=True):
            if self._location == entry.data.get(CONF_URL):
                return self.async_abort(reason="already_configured")
            if self._mac and self._mac == entry.data.get(CONF_MAC):
                return self.async_abort(reason="already_configured")

        self.context["title_placeholders"] = {"name": self._name}

        return await self.async_step_confirm()