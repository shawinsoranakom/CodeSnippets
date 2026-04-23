async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by discovery."""
        ssdp_location: ParseResult = urlparse(discovery_info.ssdp_location or "")
        host = ssdp_location.hostname
        if not host or ipaddress.ip_address(host).is_link_local:
            return self.async_abort(reason="ignore_ip6_link_local")

        self._host = host
        self._name = (
            discovery_info.upnp.get(ATTR_UPNP_FRIENDLY_NAME)
            or discovery_info.upnp[ATTR_UPNP_MODEL_NAME]
        )

        uuid: str | None
        if uuid := discovery_info.upnp.get(ATTR_UPNP_UDN):
            uuid = uuid.removeprefix("uuid:")
            await self.async_set_unique_id(uuid)
            self._abort_if_unique_id_configured({CONF_HOST: self._host})

        if self.hass.config_entries.flow.async_has_matching_flow(self):
            return self.async_abort(reason="already_in_progress")

        if entry := await self.async_check_configured_entry():
            if uuid and not entry.unique_id:
                self.hass.config_entries.async_update_entry(entry, unique_id=uuid)
            return self.async_abort(reason="already_configured")

        self.context.update(
            {
                "title_placeholders": {"name": self._name.replace("FRITZ!Box ", "")},
                "configuration_url": f"http://{self._host}",
            }
        )

        return await self.async_step_confirm()