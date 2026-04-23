async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )
        errors: dict[str, str] = {}
        self._async_abort_entries_match(
            {CONF_CALENDAR_NAME: user_input[CONF_CALENDAR_NAME]}
        )
        if user_input[CONF_URL].startswith("webcal://"):
            user_input[CONF_URL] = user_input[CONF_URL].replace(
                "webcal://", "https://", 1
            )
        self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})
        client = get_async_client(self.hass, verify_ssl=user_input[CONF_VERIFY_SSL])
        try:
            res = await get_calendar(client, user_input[CONF_URL])
            if res.status_code == HTTPStatus.UNAUTHORIZED:
                www_auth = res.headers.get("www-authenticate", "").lower()
                if "basic" in www_auth:
                    self.data = user_input
                    return await self.async_step_auth()
            if res.status_code == HTTPStatus.FORBIDDEN:
                errors["base"] = "forbidden"
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_USER_DATA_SCHEMA,
                    errors=errors,
                )
            res.raise_for_status()
        except TimeoutException as err:
            errors["base"] = "timeout_connect"
            _LOGGER.debug(
                "A timeout error occurred: %s", str(err) or type(err).__name__
            )
        except (HTTPError, InvalidURL) as err:
            errors["base"] = "cannot_connect"
            _LOGGER.debug("An error occurred: %s", str(err) or type(err).__name__)
        else:
            try:
                await parse_calendar(self.hass, res.text)
            except InvalidIcsException:
                errors["base"] = "invalid_ics_file"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_CALENDAR_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )