async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}
        if user_input is not None:
            options_input = {CONF_SOURCES: user_input[CONF_SOURCES]}
            return self.async_create_entry(title="", data=options_input)
        # Get sources
        sources_list = []
        try:
            client = await async_control_connect(self.hass, self.host, self.key)
            sources_list = get_sources(client.tv_state)
        except WebOsTvPairError:
            errors["base"] = "error_pairing"
        except WEBOSTV_EXCEPTIONS:
            errors["base"] = "cannot_connect"

        option_sources = self.config_entry.options.get(CONF_SOURCES, [])
        sources = [s for s in option_sources if s in sources_list]
        if not sources:
            sources = sources_list

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SOURCES,
                    description={"suggested_value": sources},
                ): cv.multi_select({source: source for source in sources_list}),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )