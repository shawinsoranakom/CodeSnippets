async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the user step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key: str = user_input[CONF_API_KEY]
            ferry_from: str = user_input[CONF_FROM]
            ferry_to: str = user_input.get(CONF_TO, "")
            ferry_time: str = user_input[CONF_TIME]
            weekdays: list[str] = user_input[CONF_WEEKDAY]

            name = f"{ferry_from}"
            if ferry_to:
                name = name + f" to {ferry_to}"
            if ferry_time != "00:00:00":
                name = name + f" at {ferry_time!s}"

            try:
                await self.validate_input(api_key, ferry_from, ferry_to)
            except InvalidAuthentication:
                errors["base"] = "invalid_auth"
            except NoFerryFound:
                errors["base"] = "invalid_route"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                if not errors:
                    unique_id = create_unique_id(
                        ferry_from,
                        ferry_to,
                        ferry_time,
                        weekdays,
                    )
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_API_KEY: api_key,
                            CONF_NAME: name,
                            CONF_FROM: ferry_from,
                            CONF_TO: ferry_to,
                            CONF_TIME: ferry_time,
                            CONF_WEEKDAY: weekdays,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )