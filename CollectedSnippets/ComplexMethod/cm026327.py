async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        planes_count = len(
            self.config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
        )

        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            if planes_count > 1 and not api_key:
                errors[CONF_API_KEY] = "api_key_required"
            elif api_key and RE_API_KEY.match(api_key) is None:
                errors[CONF_API_KEY] = "invalid_api_key"
            else:
                return self.async_create_entry(
                    title="", data=user_input | {CONF_API_KEY: api_key or None}
                )

        suggested_api_key = self.config_entry.options.get(CONF_API_KEY, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_KEY,
                        default=suggested_api_key,
                    )
                    if planes_count > 1
                    else vol.Optional(
                        CONF_API_KEY,
                        description={"suggested_value": suggested_api_key},
                    ): str,
                    vol.Optional(
                        CONF_DAMPING_MORNING,
                        default=self.config_entry.options.get(
                            CONF_DAMPING_MORNING, DEFAULT_DAMPING
                        ),
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=1,
                                step=0.01,
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(float),
                    ),
                    vol.Optional(
                        CONF_DAMPING_EVENING,
                        default=self.config_entry.options.get(
                            CONF_DAMPING_EVENING, DEFAULT_DAMPING
                        ),
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=0,
                                max=1,
                                step=0.01,
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(float),
                    ),
                    vol.Optional(
                        CONF_INVERTER_SIZE,
                        description={
                            "suggested_value": self.config_entry.options.get(
                                CONF_INVERTER_SIZE
                            )
                        },
                    ): vol.All(
                        selector.NumberSelector(
                            selector.NumberSelectorConfig(
                                min=1,
                                step=1,
                                mode=selector.NumberSelectorMode.BOX,
                            ),
                        ),
                        vol.Coerce(int),
                    ),
                }
            ),
            errors=errors,
        )