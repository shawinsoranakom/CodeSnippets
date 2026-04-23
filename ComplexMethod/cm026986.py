async def async_step_esphome(
        self, discovery_info: ESPHomeServiceInfo
    ) -> ConfigFlowResult:
        """Handle a ESPHome discovery."""
        if not is_hassio(self.hass):
            return self.async_abort(reason="not_hassio")

        if discovery_info.zwave_home_id:
            existing_entry: ConfigEntry | None = None
            if (
                (
                    current_config_entries := self._async_current_entries(
                        include_ignore=False
                    )
                )
                and (home_id := str(discovery_info.zwave_home_id))
                and (
                    existing_entry := next(
                        (
                            entry
                            for entry in current_config_entries
                            if entry.unique_id == home_id
                        ),
                        None,
                    )
                )
            ):
                # We can't migrate entries that are not using the add-on
                if not existing_entry.data.get(CONF_USE_ADDON):
                    return self.async_abort(reason="already_configured")

                # Only update config automatically if using socket
                if existing_entry.data.get(CONF_SOCKET_PATH):
                    manager = get_addon_manager(self.hass)
                    await self._async_set_addon_config(
                        {CONF_ADDON_SOCKET: discovery_info.socket_path}
                    )
                    if self.restart_addon:
                        await manager.async_stop_addon()
                    self.hass.config_entries.async_update_entry(
                        existing_entry,
                        data={
                            **existing_entry.data,
                            CONF_SOCKET_PATH: discovery_info.socket_path,
                        },
                    )
                    self.hass.config_entries.async_schedule_reload(
                        existing_entry.entry_id
                    )
                    return self.async_abort(reason="already_configured")

            # We are not aborting if home ID configured here, we just want to make sure that it's set
            # We will update a USB based config entry automatically in `async_step_finish_addon_setup_user`
            await self.async_set_unique_id(
                str(discovery_info.zwave_home_id), raise_on_progress=False
            )

        self.socket_path = discovery_info.socket_path
        self.context["title_placeholders"] = {
            CONF_NAME: f"{discovery_info.name} via ESPHome"
        }
        self._adapter_discovered = True

        return await self.async_step_installation_type()