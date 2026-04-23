async def async_step_configure_addon_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for config for Z-Wave JS add-on."""
        addon_info = await self._async_get_addon_info()
        addon_config = addon_info.options

        if user_input is not None:
            self.s0_legacy_key = user_input[CONF_S0_LEGACY_KEY]
            self.s2_access_control_key = user_input[CONF_S2_ACCESS_CONTROL_KEY]
            self.s2_authenticated_key = user_input[CONF_S2_AUTHENTICATED_KEY]
            self.s2_unauthenticated_key = user_input[CONF_S2_UNAUTHENTICATED_KEY]
            self.lr_s2_access_control_key = user_input[CONF_LR_S2_ACCESS_CONTROL_KEY]
            self.lr_s2_authenticated_key = user_input[CONF_LR_S2_AUTHENTICATED_KEY]
            self.usb_path = user_input.get(CONF_USB_PATH)
            self.socket_path = user_input.get(CONF_SOCKET_PATH)

            addon_config_updates = {
                CONF_ADDON_DEVICE: self.usb_path,
                CONF_ADDON_SOCKET: self.socket_path,
                CONF_ADDON_S0_LEGACY_KEY: self.s0_legacy_key,
                CONF_ADDON_S2_ACCESS_CONTROL_KEY: self.s2_access_control_key,
                CONF_ADDON_S2_AUTHENTICATED_KEY: self.s2_authenticated_key,
                CONF_ADDON_S2_UNAUTHENTICATED_KEY: self.s2_unauthenticated_key,
                CONF_ADDON_LR_S2_ACCESS_CONTROL_KEY: self.lr_s2_access_control_key,
                CONF_ADDON_LR_S2_AUTHENTICATED_KEY: self.lr_s2_authenticated_key,
            }

            addon_config_updates = self._addon_config_updates | addon_config_updates
            self._addon_config_updates = {}

            await self._async_set_addon_config(addon_config_updates)

            if addon_info.state == AddonState.RUNNING and not self.restart_addon:
                return await self.async_step_finish_addon_setup_reconfigure()

            if (
                config_entry := self._reconfigure_config_entry
            ) and config_entry.data.get(CONF_USE_ADDON):
                # Disconnect integration before restarting add-on.
                await self.hass.config_entries.async_unload(config_entry.entry_id)

            return await self.async_step_start_addon()

        usb_path = addon_config.get(CONF_ADDON_DEVICE, self.usb_path or "")
        socket_path = addon_config.get(CONF_ADDON_SOCKET, self.socket_path or "")
        s0_legacy_key = addon_config.get(
            CONF_ADDON_S0_LEGACY_KEY, self.s0_legacy_key or ""
        )
        s2_access_control_key = addon_config.get(
            CONF_ADDON_S2_ACCESS_CONTROL_KEY, self.s2_access_control_key or ""
        )
        s2_authenticated_key = addon_config.get(
            CONF_ADDON_S2_AUTHENTICATED_KEY, self.s2_authenticated_key or ""
        )
        s2_unauthenticated_key = addon_config.get(
            CONF_ADDON_S2_UNAUTHENTICATED_KEY, self.s2_unauthenticated_key or ""
        )
        lr_s2_access_control_key = addon_config.get(
            CONF_ADDON_LR_S2_ACCESS_CONTROL_KEY, self.lr_s2_access_control_key or ""
        )
        lr_s2_authenticated_key = addon_config.get(
            CONF_ADDON_LR_S2_AUTHENTICATED_KEY, self.lr_s2_authenticated_key or ""
        )

        try:
            ports = await async_get_usb_ports(self.hass)
        except OSError as err:
            _LOGGER.error("Failed to get USB ports: %s", err)
            return self.async_abort(reason="usb_ports_failed")

        # Insert empty option in ports to allow setting a socket
        ports = {
            "": "Use Socket",
            **ports,
        }

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_USB_PATH, description={"suggested_value": usb_path}
                ): vol.In(ports),
                vol.Optional(
                    CONF_SOCKET_PATH, description={"suggested_value": socket_path}
                ): str,
                vol.Optional(
                    CONF_S0_LEGACY_KEY, description={"suggested_value": s0_legacy_key}
                ): str,
                vol.Optional(
                    CONF_S2_ACCESS_CONTROL_KEY,
                    description={"suggested_value": s2_access_control_key},
                ): str,
                vol.Optional(
                    CONF_S2_AUTHENTICATED_KEY,
                    description={"suggested_value": s2_authenticated_key},
                ): str,
                vol.Optional(
                    CONF_S2_UNAUTHENTICATED_KEY,
                    description={"suggested_value": s2_unauthenticated_key},
                ): str,
                vol.Optional(
                    CONF_LR_S2_ACCESS_CONTROL_KEY,
                    description={"suggested_value": lr_s2_access_control_key},
                ): str,
                vol.Optional(
                    CONF_LR_S2_AUTHENTICATED_KEY,
                    description={"suggested_value": lr_s2_authenticated_key},
                ): str,
            }
        )

        return self.async_show_form(
            step_id="configure_addon_reconfigure", data_schema=data_schema
        )