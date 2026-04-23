async def async_step_options_digital(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to configure the IO options for digital sensors."""
        errors: dict[str, str] = {}
        if user_input is not None and self.active_cfg is not None:
            zone = {"zone": self.active_cfg}
            zone.update(user_input)
            self.new_opt[CONF_SENSORS] = [*self.new_opt.get(CONF_SENSORS, []), zone]
            self.io_cfg.pop(self.active_cfg)
            self.active_cfg = None

        if self.active_cfg:
            current_cfg = self.get_current_cfg(CONF_SENSORS, self.active_cfg)
            return self.async_show_form(
                step_id="options_digital",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_TYPE, default=current_cfg.get(CONF_TYPE, "dht")
                        ): vol.All(vol.Lower, vol.In(["dht", "ds18b20"])),
                        vol.Optional(
                            CONF_NAME, default=current_cfg.get(CONF_NAME, vol.UNDEFINED)
                        ): str,
                        vol.Optional(
                            CONF_POLL_INTERVAL,
                            default=current_cfg.get(CONF_POLL_INTERVAL, 3),
                        ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    }
                ),
                description_placeholders={
                    "zone": f"Zone {self.active_cfg}"
                    if len(self.active_cfg) < 3
                    else self.active_cfg.upper()
                },
                errors=errors,
            )

        # find the next unconfigured digital sensor
        for key, value in self.io_cfg.items():
            if value == CONF_IO_DIG:
                self.active_cfg = key
                current_cfg = self.get_current_cfg(CONF_SENSORS, self.active_cfg)
                return self.async_show_form(
                    step_id="options_digital",
                    data_schema=vol.Schema(
                        {
                            vol.Required(
                                CONF_TYPE, default=current_cfg.get(CONF_TYPE, "dht")
                            ): vol.All(vol.Lower, vol.In(["dht", "ds18b20"])),
                            vol.Optional(
                                CONF_NAME,
                                default=current_cfg.get(CONF_NAME, vol.UNDEFINED),
                            ): str,
                            vol.Optional(
                                CONF_POLL_INTERVAL,
                                default=current_cfg.get(CONF_POLL_INTERVAL, 3),
                            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                        }
                    ),
                    description_placeholders={
                        "zone": f"Zone {self.active_cfg}"
                        if len(self.active_cfg) < 3
                        else self.active_cfg.upper()
                    },
                    errors=errors,
                )

        return await self.async_step_options_switch()