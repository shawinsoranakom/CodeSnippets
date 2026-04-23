async def async_step_finish_addon_setup_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Prepare info needed to complete the config entry.

        Get add-on discovery info and server version info.
        Set unique id and abort if already configured.
        """
        if not self.ws_address:
            discovery_info = await self._async_get_addon_discovery_info()
            self.ws_address = f"ws://{discovery_info['host']}:{discovery_info['port']}"

        if not self.unique_id or self.source == SOURCE_USB:
            if not self.version_info:
                try:
                    self.version_info = await async_get_version_info(
                        self.hass, self.ws_address
                    )
                except CannotConnect as err:
                    raise AbortFlow("cannot_connect") from err

            await self.async_set_unique_id(
                str(self.version_info.home_id), raise_on_progress=False
            )

        # When we came from discovery, make sure we update the add-on
        if self._adapter_discovered and self.use_addon:
            await self._async_set_addon_config(
                {
                    CONF_ADDON_DEVICE: self.usb_path,
                    CONF_ADDON_SOCKET: self.socket_path,
                    CONF_ADDON_S0_LEGACY_KEY: self.s0_legacy_key,
                    CONF_ADDON_S2_ACCESS_CONTROL_KEY: self.s2_access_control_key,
                    CONF_ADDON_S2_AUTHENTICATED_KEY: self.s2_authenticated_key,
                    CONF_ADDON_S2_UNAUTHENTICATED_KEY: self.s2_unauthenticated_key,
                    CONF_ADDON_LR_S2_ACCESS_CONTROL_KEY: self.lr_s2_access_control_key,
                    CONF_ADDON_LR_S2_AUTHENTICATED_KEY: self.lr_s2_authenticated_key,
                }
            )
            if self.restart_addon:
                manager = get_addon_manager(self.hass)
                await manager.async_stop_addon()

        self._abort_if_unique_id_configured(
            updates={
                CONF_URL: self.ws_address,
                CONF_USB_PATH: self.usb_path,
                CONF_SOCKET_PATH: self.socket_path,
                CONF_S0_LEGACY_KEY: self.s0_legacy_key,
                CONF_S2_ACCESS_CONTROL_KEY: self.s2_access_control_key,
                CONF_S2_AUTHENTICATED_KEY: self.s2_authenticated_key,
                CONF_S2_UNAUTHENTICATED_KEY: self.s2_unauthenticated_key,
                CONF_LR_S2_ACCESS_CONTROL_KEY: self.lr_s2_access_control_key,
                CONF_LR_S2_AUTHENTICATED_KEY: self.lr_s2_authenticated_key,
            },
            error=(
                "migration_successful"
                if self.source in (SOURCE_USB, SOURCE_ESPHOME)
                else "already_configured"
            ),
        )
        return self._async_create_entry_from_vars()