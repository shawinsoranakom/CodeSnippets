async def async_step_initial(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key: str = user_input[CONF_API_KEY]
            train_from: str = user_input[CONF_FROM]
            train_to: str = user_input[CONF_TO]
            train_time: str | None = user_input.get(CONF_TIME)
            train_days: list = user_input[CONF_WEEKDAY]
            filter_product: str | None = user_input[CONF_FILTER_PRODUCT]

            if filter_product == "":
                filter_product = None

            name = f"{train_from} to {train_to}"
            if train_time:
                name = f"{train_from} to {train_to} at {train_time}"

            self._from_stations, from_errors = await validate_station(
                self.hass, api_key, train_from, CONF_FROM
            )
            self._to_stations, to_errors = await validate_station(
                self.hass, api_key, train_to, CONF_TO
            )
            errors = {**from_errors, **to_errors}

            if not errors:
                if len(self._from_stations) == 1 and len(self._to_stations) == 1:
                    self._async_abort_entries_match(
                        {
                            CONF_API_KEY: api_key,
                            CONF_FROM: self._from_stations[0].signature,
                            CONF_TO: self._to_stations[0].signature,
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
                                CONF_FROM: self._from_stations[0].signature,
                                CONF_TO: self._to_stations[0].signature,
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
                            CONF_FROM: self._from_stations[0].signature,
                            CONF_TO: self._to_stations[0].signature,
                            CONF_TIME: train_time,
                            CONF_WEEKDAY: train_days,
                        },
                        options={CONF_FILTER_PRODUCT: filter_product},
                    )
                self._data = user_input
                return await self.async_step_select_stations()

        return self.async_show_form(
            step_id="initial",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA, user_input or {}
            ),
            errors=errors,
        )