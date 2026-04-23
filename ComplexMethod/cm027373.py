async def async_step_select_stations(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the select station step."""
        if user_input is not None:
            api_key: str = self._data[CONF_API_KEY]
            train_from: str = (
                user_input.get(CONF_FROM) or self._from_stations[0].signature
            )
            train_to: str = user_input.get(CONF_TO) or self._to_stations[0].signature
            train_time: str | None = self._data.get(CONF_TIME)
            train_days: list = self._data[CONF_WEEKDAY]
            filter_product: str | None = self._data[CONF_FILTER_PRODUCT]

            if filter_product == "":
                filter_product = None

            name = f"{self._data[CONF_FROM]} to {self._data[CONF_TO]}"
            if train_time:
                name = (
                    f"{self._data[CONF_FROM]} to {self._data[CONF_TO]} at {train_time}"
                )
            self._async_abort_entries_match(
                {
                    CONF_API_KEY: api_key,
                    CONF_FROM: train_from,
                    CONF_TO: train_to,
                    CONF_TIME: train_time,
                    CONF_WEEKDAY: train_days,
                    CONF_FILTER_PRODUCT: filter_product,
                }
            )
            if self.source == SOURCE_RECONFIGURE:
                reconfigure_entry = self._get_reconfigure_entry()
                return self.async_update_reload_and_abort(
                    reconfigure_entry,
                    title=name,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_NAME: name,
                        CONF_FROM: train_from,
                        CONF_TO: train_to,
                        CONF_TIME: train_time,
                        CONF_WEEKDAY: train_days,
                    },
                    options={CONF_FILTER_PRODUCT: filter_product},
                )
            return self.async_create_entry(
                title=name,
                data={
                    CONF_API_KEY: api_key,
                    CONF_NAME: name,
                    CONF_FROM: train_from,
                    CONF_TO: train_to,
                    CONF_TIME: train_time,
                    CONF_WEEKDAY: train_days,
                },
                options={CONF_FILTER_PRODUCT: filter_product},
            )
        from_options = [
            SelectOptionDict(value=station.signature, label=station.station_name)
            for station in self._from_stations
        ]
        to_options = [
            SelectOptionDict(value=station.signature, label=station.station_name)
            for station in self._to_stations
        ]
        schema = {}
        if len(from_options) > 1:
            schema[vol.Required(CONF_FROM)] = SelectSelector(
                SelectSelectorConfig(
                    options=from_options, mode=SelectSelectorMode.DROPDOWN, sort=True
                )
            )
        if len(to_options) > 1:
            schema[vol.Required(CONF_TO)] = SelectSelector(
                SelectSelectorConfig(
                    options=to_options, mode=SelectSelectorMode.DROPDOWN, sort=True
                )
            )

        return self.async_show_form(
            step_id="select_stations",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(schema), user_input or {}
            ),
        )