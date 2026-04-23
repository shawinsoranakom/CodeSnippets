async def async_step_options_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow the user to configure the IO options for switches."""
        errors: dict[str, str] = {}
        if user_input is not None and self.active_cfg is not None:
            zone = {"zone": self.active_cfg}
            zone.update(user_input)
            del zone[CONF_MORE_STATES]
            self.new_opt[CONF_SWITCHES] = [*self.new_opt.get(CONF_SWITCHES, []), zone]

            # iterate through multiple switch states
            if self.current_states:
                self.current_states.pop(0)

            # only go to next zone if all states are entered
            self.current_state += 1
            if user_input[CONF_MORE_STATES] == CONF_NO:
                self.io_cfg.pop(self.active_cfg)
                self.active_cfg = None

        if self.active_cfg:
            current_cfg = next(iter(self.current_states), {})
            return self.async_show_form(
                step_id="options_switch",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_NAME, default=current_cfg.get(CONF_NAME, vol.UNDEFINED)
                        ): str,
                        vol.Optional(
                            CONF_ACTIVATION,
                            default=current_cfg.get(CONF_ACTIVATION, STATE_HIGH),
                        ): vol.All(vol.Lower, vol.In([STATE_HIGH, STATE_LOW])),
                        vol.Optional(
                            CONF_MOMENTARY,
                            default=current_cfg.get(CONF_MOMENTARY, vol.UNDEFINED),
                        ): vol.All(vol.Coerce(int), vol.Range(min=10)),
                        vol.Optional(
                            CONF_PAUSE,
                            default=current_cfg.get(CONF_PAUSE, vol.UNDEFINED),
                        ): vol.All(vol.Coerce(int), vol.Range(min=10)),
                        vol.Optional(
                            CONF_REPEAT,
                            default=current_cfg.get(CONF_REPEAT, vol.UNDEFINED),
                        ): vol.All(vol.Coerce(int), vol.Range(min=-1)),
                        vol.Required(
                            CONF_MORE_STATES,
                            default=CONF_YES
                            if len(self.current_states) > 1
                            else CONF_NO,
                        ): vol.In([CONF_YES, CONF_NO]),
                    }
                ),
                description_placeholders={
                    "zone": f"Zone {self.active_cfg}"
                    if len(self.active_cfg) < 3
                    else self.active_cfg.upper(),
                    "state": str(self.current_state),
                },
                errors=errors,
            )

        # find the next unconfigured switch
        for key, value in self.io_cfg.items():
            if value == CONF_IO_SWI:
                self.active_cfg = key
                self.current_states = [
                    cfg
                    for cfg in self.current_opt.get(CONF_SWITCHES, [])
                    if cfg[CONF_ZONE] == self.active_cfg
                ]
                current_cfg = next(iter(self.current_states), {})
                self.current_state = 1
                return self.async_show_form(
                    step_id="options_switch",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(
                                CONF_NAME,
                                default=current_cfg.get(CONF_NAME, vol.UNDEFINED),
                            ): str,
                            vol.Optional(
                                CONF_ACTIVATION,
                                default=current_cfg.get(CONF_ACTIVATION, STATE_HIGH),
                            ): vol.In(["low", "high"]),
                            vol.Optional(
                                CONF_MOMENTARY,
                                default=current_cfg.get(CONF_MOMENTARY, vol.UNDEFINED),
                            ): vol.All(vol.Coerce(int), vol.Range(min=10)),
                            vol.Optional(
                                CONF_PAUSE,
                                default=current_cfg.get(CONF_PAUSE, vol.UNDEFINED),
                            ): vol.All(vol.Coerce(int), vol.Range(min=10)),
                            vol.Optional(
                                CONF_REPEAT,
                                default=current_cfg.get(CONF_REPEAT, vol.UNDEFINED),
                            ): vol.All(vol.Coerce(int), vol.Range(min=-1)),
                            vol.Required(
                                CONF_MORE_STATES,
                                default=CONF_YES
                                if len(self.current_states) > 1
                                else CONF_NO,
                            ): vol.In([CONF_YES, CONF_NO]),
                        }
                    ),
                    description_placeholders={
                        "zone": f"Zone {self.active_cfg}"
                        if len(self.active_cfg) < 3
                        else self.active_cfg.upper(),
                        "state": str(self.current_state),
                    },
                    errors=errors,
                )

        return await self.async_step_options_misc()