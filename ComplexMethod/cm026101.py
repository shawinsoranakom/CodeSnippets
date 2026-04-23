async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle a flow initialized by ssdp discovery."""
        LOGGER.debug("Samsung device found via SSDP: %s", discovery_info)
        model_name: str = discovery_info.upnp.get(ATTR_UPNP_MODEL_NAME) or ""
        if discovery_info.ssdp_st == UPNP_SVC_RENDERING_CONTROL:
            self._ssdp_rendering_control_location = discovery_info.ssdp_location
            LOGGER.debug(
                "Set SSDP RenderingControl location to: %s",
                self._ssdp_rendering_control_location,
            )
        elif discovery_info.ssdp_st == UPNP_SVC_MAIN_TV_AGENT:
            self._ssdp_main_tv_agent_location = discovery_info.ssdp_location
            LOGGER.debug(
                "Set SSDP MainTvAgent location to: %s",
                self._ssdp_main_tv_agent_location,
            )
        self._udn = self._upnp_udn = _strip_uuid(discovery_info.upnp[ATTR_UPNP_UDN])
        if hostname := urlparse(discovery_info.ssdp_location or "").hostname:
            self._host = hostname
        self._manufacturer = discovery_info.upnp.get(ATTR_UPNP_MANUFACTURER)
        self._abort_if_manufacturer_is_not_samsung()

        # Set defaults, in case they cannot be extracted from device_info
        self._name = self._title = self._model = model_name
        # Update from device_info (if accessible)
        await self._async_get_and_check_device_info()

        # The UDN provided by the ssdp discovery doesn't always match the UDN
        # from the device_info, used by the other methods so we need to
        # ensure the device_info is loaded before setting the unique_id
        await self._async_set_unique_id_from_udn()
        self._async_update_and_abort_for_matching_unique_id()
        self._async_abort_if_host_already_in_progress()
        if self._method == METHOD_LEGACY and discovery_info.ssdp_st in (
            UPNP_SVC_RENDERING_CONTROL,
            UPNP_SVC_MAIN_TV_AGENT,
        ):
            # The UDN we use for the unique id cannot be determined
            # from device_info for legacy devices
            return self.async_abort(reason="not_supported")
        self.context["title_placeholders"] = {"device": self._title}
        return await self.async_step_confirm()