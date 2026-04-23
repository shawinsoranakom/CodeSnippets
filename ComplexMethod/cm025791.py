async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Process entity discovered via SSDP."""

        device_url = discovery_info.ssdp_location
        if device_url is None:
            return self.async_abort(reason="cannot_connect")

        device_hostname = hostname_from_url(device_url)
        for entry in self._async_current_entries(include_ignore=False):
            if device_hostname == hostname_from_url(entry.data[CONF_WEBFSAPI_URL]):
                return self.async_abort(reason="already_configured")

        if speaker_name := discovery_info.ssdp_headers.get(SSDP_ATTR_SPEAKER_NAME):
            # If we have a name, use it as flow title
            self.context["title_placeholders"] = {"name": speaker_name}

        try:
            self._webfsapi_url = await AFSAPI.get_webfsapi_endpoint(device_url)
        except FSConnectionError:
            return self.async_abort(reason="cannot_connect")
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return self.async_abort(reason="unknown")

        # try to login with default pin
        afsapi = AFSAPI(self._webfsapi_url, DEFAULT_PIN)
        try:
            await afsapi.get_friendly_name()
        except InvalidPinError:
            return self.async_abort(reason="invalid_auth")

        try:
            unique_id = await afsapi.get_radio_id()
        except FSNotImplementedError:
            unique_id = None

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(
            updates={CONF_WEBFSAPI_URL: self._webfsapi_url}, reload_on_update=True
        )

        self._name = await afsapi.get_friendly_name()

        return await self.async_step_confirm()