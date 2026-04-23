async def async_step_pair_tv(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start pairing process for TV.

        Ask user for PIN to complete pairing process.
        """
        errors: dict[str, str] = {}
        assert self._data

        # Start pairing process if it hasn't already started
        if not self._ch_type and not self._pairing_token:
            dev = VizioAsync(
                DEVICE_ID,
                self._data[CONF_HOST],
                self._data[CONF_NAME],
                None,
                self._data[CONF_DEVICE_CLASS],
                session=async_get_clientsession(self.hass, False),
            )
            pair_data = await dev.start_pair()

            if pair_data:
                self._ch_type = pair_data.ch_type
                self._pairing_token = pair_data.token
                return await self.async_step_pair_tv()

            return self.async_show_form(
                step_id="user",
                data_schema=_get_config_schema(self._data),
                errors={"base": "cannot_connect"},
            )

        # Complete pairing process if PIN has been provided
        if user_input and user_input.get(CONF_PIN):
            dev = VizioAsync(
                DEVICE_ID,
                self._data[CONF_HOST],
                self._data[CONF_NAME],
                None,
                self._data[CONF_DEVICE_CLASS],
                session=async_get_clientsession(self.hass, False),
            )
            pair_data = await dev.pair(
                self._ch_type, self._pairing_token, user_input[CONF_PIN]
            )

            if pair_data:
                self._data[CONF_ACCESS_TOKEN] = pair_data.auth_token
                self._must_show_form = True
                return await self.async_step_pairing_complete()

            # If no data was retrieved, it's assumed that the pairing attempt was not
            # successful
            errors[CONF_PIN] = "complete_pairing_failed"

        return self.async_show_form(
            step_id="pair_tv",
            data_schema=_get_pairing_schema(user_input),
            errors=errors,
        )