async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}
        if not self.departure_filters:
            departure_list = {}
            hub = self.config_entry.runtime_data

            try:
                departure_list = await hub.gti.departureList(
                    {
                        "station": {
                            "type": "STATION",
                            "id": self.config_entry.data[CONF_STATION].get("id"),
                        },
                        "time": {"date": "heute", "time": "jetzt"},
                        "maxList": 5,
                        "maxTimeOffset": 200,
                        "useRealtime": True,
                        "returnFilters": True,
                    }
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"

            if not errors:
                self.departure_filters = {
                    str(i): departure_filter
                    for i, departure_filter in enumerate(departure_list["filter"])
                }

        if user_input is not None and not errors:
            options = {
                CONF_FILTER: [
                    self.departure_filters[x] for x in user_input[CONF_FILTER]
                ],
                CONF_OFFSET: user_input[CONF_OFFSET],
                CONF_REAL_TIME: user_input[CONF_REAL_TIME],
            }

            return self.async_create_entry(title="", data=options)

        if CONF_FILTER in self.config_entry.options:
            old_filter = [
                i
                for (i, f) in self.departure_filters.items()
                if f in self.config_entry.options[CONF_FILTER]
            ]
        else:
            old_filter = []

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_FILTER, default=old_filter): cv.multi_select(
                        {
                            key: (
                                f"{departure_filter['serviceName']},"
                                f" {departure_filter['label']}"
                            )
                            for key, departure_filter in self.departure_filters.items()
                        }
                    ),
                    vol.Required(
                        CONF_OFFSET,
                        default=self.config_entry.options.get(CONF_OFFSET, 0),
                    ): cv.positive_int,
                    vol.Optional(
                        CONF_REAL_TIME,
                        default=self.config_entry.options.get(CONF_REAL_TIME, True),
                    ): bool,
                }
            ),
            errors=errors,
        )