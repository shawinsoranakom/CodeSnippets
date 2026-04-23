async def async_step_options_binary(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to configure the IO options for binary sensors."""
        errors: dict[str, str] = {}
        if user_input is not None and self.active_cfg is not None:
            zone = {"zone": self.active_cfg}
            zone.update(user_input)
            self.new_opt[CONF_BINARY_SENSORS] = [
                *self.new_opt.get(CONF_BINARY_SENSORS, []),
                zone,
            ]
            self.io_cfg.pop(self.active_cfg)
            self.active_cfg = None

        if self.active_cfg:
            current_cfg = self.get_current_cfg(CONF_BINARY_SENSORS, self.active_cfg)
            return self.async_show_form(
                step_id="options_binary",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_TYPE,
                            default=current_cfg.get(
                                CONF_TYPE, BinarySensorDeviceClass.DOOR
                            ),
                        ): DEVICE_CLASSES_SCHEMA,
                        vol.Optional(
                            CONF_NAME, default=current_cfg.get(CONF_NAME, vol.UNDEFINED)
                        ): str,
                        vol.Optional(
                            CONF_INVERSE, default=current_cfg.get(CONF_INVERSE, False)
                        ): bool,
                    }
                ),
                description_placeholders={
                    "zone": f"Zone {self.active_cfg}"
                    if len(self.active_cfg) < 3
                    else self.active_cfg.upper()
                },
                errors=errors,
            )

        # find the next unconfigured binary sensor
        for key, value in self.io_cfg.items():
            if value == CONF_IO_BIN:
                self.active_cfg = key
                current_cfg = self.get_current_cfg(CONF_BINARY_SENSORS, self.active_cfg)
                return self.async_show_form(
                    step_id="options_binary",
                    data_schema=vol.Schema(
                        {
                            vol.Required(
                                CONF_TYPE,
                                default=current_cfg.get(
                                    CONF_TYPE, BinarySensorDeviceClass.DOOR
                                ),
                            ): DEVICE_CLASSES_SCHEMA,
                            vol.Optional(
                                CONF_NAME,
                                default=current_cfg.get(CONF_NAME, vol.UNDEFINED),
                            ): str,
                            vol.Optional(
                                CONF_INVERSE,
                                default=current_cfg.get(CONF_INVERSE, False),
                            ): bool,
                        }
                    ),
                    description_placeholders={
                        "zone": f"Zone {self.active_cfg}"
                        if len(self.active_cfg) < 3
                        else self.active_cfg.upper()
                    },
                    errors=errors,
                )

        return await self.async_step_options_digital()