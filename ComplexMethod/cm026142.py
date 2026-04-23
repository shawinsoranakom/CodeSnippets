def _ssdp_listener_process_callback(
        self,
        ssdp_device: SsdpDevice,
        dst: DeviceOrServiceType,
        source: SsdpSource,
        info_desc: Mapping[str, Any],
        skip_callbacks: bool = False,
    ) -> None:
        """Handle a device/service change."""
        matching_domains: set[str] = set()
        combined_headers = ssdp_device.combined_headers(dst)
        callbacks = self._async_get_matching_callbacks(combined_headers)

        # If there are no changes from a search, do not trigger a config flow
        if source != SsdpSource.SEARCH_ALIVE:
            matching_domains = self.integration_matchers.async_matching_domains(
                CaseInsensitiveDict(combined_headers.as_dict(), **info_desc)
            )

        if (
            not callbacks
            and not matching_domains
            and source != SsdpSource.ADVERTISEMENT_BYEBYE
        ):
            return

        discovery_info = discovery_info_from_headers_and_description(
            ssdp_device, combined_headers, info_desc
        )
        discovery_info.x_homeassistant_matching_domains = matching_domains

        if callbacks and not skip_callbacks:
            ssdp_change = SSDP_SOURCE_SSDP_CHANGE_MAPPING[source]
            _async_process_callbacks(self.hass, callbacks, discovery_info, ssdp_change)

        # Config flows should only be created for alive/update messages from alive devices
        if source == SsdpSource.ADVERTISEMENT_BYEBYE:
            self._async_dismiss_discoveries(discovery_info)
            return

        _LOGGER.debug("Discovery info: %s", discovery_info)

        if not matching_domains:
            return  # avoid creating DiscoveryKey if there are no matches

        discovery_key = discovery_flow.DiscoveryKey(
            domain=DOMAIN, key=ssdp_device.udn, version=1
        )
        for domain in matching_domains:
            _LOGGER.debug("Discovered %s at %s", domain, ssdp_device.location)
            discovery_flow.async_create_flow(
                self.hass,
                domain,
                {"source": config_entries.SOURCE_SSDP},
                discovery_info,
                discovery_key=discovery_key,
            )