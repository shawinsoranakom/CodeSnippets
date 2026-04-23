async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by discovery."""
        host = urlparse(discovery_info.ssdp_location).hostname
        assert isinstance(host, str)

        if (
            ipaddress.ip_address(host).version == 6
            and ipaddress.ip_address(host).is_link_local
        ):
            return self.async_abort(reason="ignore_ip6_link_local")

        if uuid := discovery_info.upnp.get(ATTR_UPNP_UDN):
            uuid = uuid.removeprefix("uuid:")
            await self.async_set_unique_id(uuid)
            self._abort_if_unique_id_configured({CONF_HOST: host})

        self._host = host
        if self.hass.config_entries.flow.async_has_matching_flow(self):
            return self.async_abort(reason="already_in_progress")

        # update old and user-configured config entries
        for entry in self._async_current_entries(include_ignore=False):
            if entry.data[CONF_HOST] == host:
                if uuid and not entry.unique_id:
                    self.hass.config_entries.async_update_entry(entry, unique_id=uuid)
                return self.async_abort(reason="already_configured")

        self._name = str(discovery_info.upnp.get(ATTR_UPNP_FRIENDLY_NAME) or host)

        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_confirm()