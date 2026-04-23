async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Prepare configuration for a discovered doorbird device."""
        macaddress = discovery_info.properties["macaddress"]

        if macaddress[:6] != DOORBIRD_OUI:
            return self.async_abort(reason="not_doorbird_device")
        if discovery_info.ip_address.is_link_local:
            return self.async_abort(reason="link_local_address")
        if discovery_info.ip_address.version != 4:
            return self.async_abort(reason="not_ipv4_address")

        await self.async_set_unique_id(macaddress)
        host = discovery_info.host

        # Check if we have an existing entry for this MAC
        existing_entry = self.hass.config_entries.async_entry_for_domain_unique_id(
            DOMAIN, macaddress
        )

        if existing_entry:
            if existing_entry.source == SOURCE_IGNORE:
                return self.async_abort(reason="already_configured")

            # Check if the host is actually changing
            if existing_entry.data.get(CONF_HOST) != host:
                await self._async_verify_existing_device_for_discovery(
                    existing_entry, host, macaddress
                )

            # All checks passed or no change needed, abort
            # if already configured with potential IP update
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._async_abort_entries_match({CONF_HOST: host})

        if not await async_verify_supported_device(self.hass, host):
            return self.async_abort(reason="not_doorbird_device")

        chop_ending = "._axis-video._tcp.local."
        friendly_hostname = discovery_info.name.removesuffix(chop_ending)

        self.context["title_placeholders"] = {
            CONF_NAME: friendly_hostname,
            CONF_HOST: host,
        }
        self.discovery_schema = _schema_with_defaults(host=host, name=friendly_hostname)

        return await self.async_step_user()