async def async_step_configure_security_keys(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for security keys for existing Z-Wave network."""
        addon_info = await self._async_get_addon_info()
        addon_config = addon_info.options

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

        if user_input is not None:
            self.s0_legacy_key = user_input.get(CONF_S0_LEGACY_KEY, s0_legacy_key)
            self.s2_access_control_key = user_input.get(
                CONF_S2_ACCESS_CONTROL_KEY, s2_access_control_key
            )
            self.s2_authenticated_key = user_input.get(
                CONF_S2_AUTHENTICATED_KEY, s2_authenticated_key
            )
            self.s2_unauthenticated_key = user_input.get(
                CONF_S2_UNAUTHENTICATED_KEY, s2_unauthenticated_key
            )
            self.lr_s2_access_control_key = user_input.get(
                CONF_LR_S2_ACCESS_CONTROL_KEY, lr_s2_access_control_key
            )
            self.lr_s2_authenticated_key = user_input.get(
                CONF_LR_S2_AUTHENTICATED_KEY, lr_s2_authenticated_key
            )

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

            self._addon_config_updates = addon_config_updates
            return await self.async_step_start_addon()

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_S0_LEGACY_KEY, default=s0_legacy_key): str,
                vol.Optional(
                    CONF_S2_ACCESS_CONTROL_KEY, default=s2_access_control_key
                ): str,
                vol.Optional(
                    CONF_S2_AUTHENTICATED_KEY, default=s2_authenticated_key
                ): str,
                vol.Optional(
                    CONF_S2_UNAUTHENTICATED_KEY, default=s2_unauthenticated_key
                ): str,
                vol.Optional(
                    CONF_LR_S2_ACCESS_CONTROL_KEY, default=lr_s2_access_control_key
                ): str,
                vol.Optional(
                    CONF_LR_S2_AUTHENTICATED_KEY, default=lr_s2_authenticated_key
                ): str,
            }
        )

        return self.async_show_form(
            step_id="configure_security_keys", data_schema=data_schema
        )