async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a discovered WiLight."""
        # Filter out basic information
        if (
            not discovery_info.ssdp_location
            or ATTR_UPNP_MANUFACTURER not in discovery_info.upnp
            or ATTR_UPNP_SERIAL not in discovery_info.upnp
            or ATTR_UPNP_MODEL_NAME not in discovery_info.upnp
            or ATTR_UPNP_MODEL_NUMBER not in discovery_info.upnp
        ):
            return self.async_abort(reason="not_wilight_device")
        # Filter out non-WiLight devices
        if discovery_info.upnp[ATTR_UPNP_MANUFACTURER] != WILIGHT_MANUFACTURER:
            return self.async_abort(reason="not_wilight_device")

        host = urlparse(discovery_info.ssdp_location).hostname
        serial_number = discovery_info.upnp[ATTR_UPNP_SERIAL]
        model_name = discovery_info.upnp[ATTR_UPNP_MODEL_NAME]

        if not self._wilight_update(host, serial_number, model_name):
            return self.async_abort(reason="not_wilight_device")

        # Check if all components of this WiLight are allowed in this version of the HA integration
        component_ok = all(
            wilight_component in ALLOWED_WILIGHT_COMPONENTS
            for wilight_component in self._wilight_components
        )

        if not component_ok:
            return self.async_abort(reason="not_supported_device")

        await self.async_set_unique_id(self._serial_number)
        self._abort_if_unique_id_configured(updates={CONF_HOST: self._host})

        self.context["title_placeholders"] = {"name": self._title}
        return await self.async_step_confirm()