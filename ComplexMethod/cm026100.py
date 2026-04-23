def _async_update_existing_matching_entry(
        self,
    ) -> ConfigEntry | None:
        """Check existing entries and update them.

        Returns the existing entry if it was updated.
        """
        entry, is_unique_match = self._async_get_existing_matching_entry()
        if not entry:
            return None
        entry_kw_args: dict = {}
        if self.unique_id and (
            entry.unique_id is None
            or (is_unique_match and self.unique_id != entry.unique_id)
        ):
            entry_kw_args["unique_id"] = self.unique_id
        data: dict[str, Any] = dict(entry.data)
        update_ssdp_rendering_control_location = (
            self._ssdp_rendering_control_location
            and data.get(CONF_SSDP_RENDERING_CONTROL_LOCATION)
            != self._ssdp_rendering_control_location
        )
        update_ssdp_main_tv_agent_location = (
            self._ssdp_main_tv_agent_location
            and data.get(CONF_SSDP_MAIN_TV_AGENT_LOCATION)
            != self._ssdp_main_tv_agent_location
        )
        update_mac = self._mac and (
            not (data_mac := data.get(CONF_MAC))
            or _mac_is_same_with_incorrect_formatting(data_mac, self._mac)
        )
        update_model = self._model and not data.get(CONF_MODEL)
        if (
            update_ssdp_rendering_control_location
            or update_ssdp_main_tv_agent_location
            or update_mac
            or update_model
        ):
            if update_ssdp_rendering_control_location:
                data[CONF_SSDP_RENDERING_CONTROL_LOCATION] = (
                    self._ssdp_rendering_control_location
                )
            if update_ssdp_main_tv_agent_location:
                data[CONF_SSDP_MAIN_TV_AGENT_LOCATION] = (
                    self._ssdp_main_tv_agent_location
                )
            if update_mac:
                data[CONF_MAC] = self._mac
            if update_model:
                data[CONF_MODEL] = self._model
            entry_kw_args["data"] = data
        if not entry_kw_args:
            return None
        LOGGER.debug("Updating existing config entry with %s", entry_kw_args)
        self.hass.config_entries.async_update_entry(entry, **entry_kw_args)
        if entry.state != ConfigEntryState.LOADED:
            # If its loaded it already has a reload listener in place
            # and we do not want to trigger multiple reloads
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(entry.entry_id)
            )
        return entry