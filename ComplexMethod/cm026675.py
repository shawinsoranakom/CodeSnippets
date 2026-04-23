async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to setup a connection between 2 stations."""

        try:
            choices = await self._fetch_stations_choices()
        except CannotConnect:
            return self.async_abort(reason="api_unavailable")

        errors: dict = {}
        if user_input is not None:
            if user_input[CONF_STATION_FROM] == user_input[CONF_STATION_TO]:
                errors["base"] = "same_station"
            else:
                [station_from] = [
                    station
                    for station in self.stations
                    if station.id == user_input[CONF_STATION_FROM]
                ]
                [station_to] = [
                    station
                    for station in self.stations
                    if station.id == user_input[CONF_STATION_TO]
                ]
                vias = "_excl_vias" if user_input.get(CONF_EXCLUDE_VIAS) else ""
                await self.async_set_unique_id(
                    f"{user_input[CONF_STATION_FROM]}_{user_input[CONF_STATION_TO]}{vias}"
                )
                self._abort_if_unique_id_configured()

                config_entry_name = f"Train from {station_from.standard_name} to {station_to.standard_name}"
                return self.async_create_entry(
                    title=config_entry_name,
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_STATION_FROM): SelectSelector(
                    SelectSelectorConfig(
                        options=choices,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_STATION_TO): SelectSelector(
                    SelectSelectorConfig(
                        options=choices,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(CONF_EXCLUDE_VIAS): BooleanSelector(),
                vol.Optional(CONF_SHOW_ON_MAP): BooleanSelector(),
            },
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )