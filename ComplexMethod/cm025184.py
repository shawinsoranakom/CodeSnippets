async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle SSDP initiated flow."""
        await self.async_set_unique_id(discovery_info.upnp[ATTR_UPNP_UDN])
        self._abort_if_unique_id_configured()

        norm_url = url_normalize(
            discovery_info.upnp.get(ATTR_UPNP_PRESENTATION_URL)
            or f"http://{urlparse(discovery_info.ssdp_location or '').hostname}/"
        )
        if TYPE_CHECKING:
            # url_normalize only returns None if passed None, and we don't do that
            assert norm_url is not None
        self.url = norm_url

        for existing_entry in (
            x for x in self._async_current_entries() if x.data[CONF_URL] == self.url
        ):
            # Update unique id of entry with the same URL
            if not existing_entry.unique_id:
                self.hass.config_entries.async_update_entry(
                    existing_entry, unique_id=discovery_info.upnp[ATTR_UPNP_UDN]
                )
            return self.async_abort(reason="already_configured")

        self.name = discovery_info.upnp.get(ATTR_UPNP_FRIENDLY_NAME, "")
        if self.name:
            # Remove trailing " (ip)" if present for consistency with user driven config
            self.name = re.sub(r"\s+\([\d.]+\)\s*$", "", self.name)

        self.context["title_placeholders"] = {CONF_NAME: self.name}
        return await self.async_step_confirm()