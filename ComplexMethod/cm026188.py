async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the authentication step."""
        if user_input is None:
            return self.async_show_form(
                step_id="auth",
                data_schema=STEP_AUTH_DATA_SCHEMA,
            )

        errors: dict[str, str] = {}
        client = get_async_client(self.hass, verify_ssl=self.data[CONF_VERIFY_SSL])
        try:
            res = await get_calendar(
                client,
                self.data[CONF_URL],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
            )
            if res.status_code == HTTPStatus.UNAUTHORIZED:
                errors["base"] = "invalid_auth"
            elif res.status_code == HTTPStatus.FORBIDDEN:
                return self.async_abort(reason="forbidden")
            else:
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
            if not errors:
                try:
                    await parse_calendar(self.hass, res.text)
                except InvalidIcsException:
                    return self.async_abort(reason="invalid_ics_file")
                else:
                    return self.async_create_entry(
                        title=self.data[CONF_CALENDAR_NAME],
                        data={
                            **self.data,
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                        },
                    )

        return self.async_show_form(
            step_id="auth",
            data_schema=self.add_suggested_values_to_schema(
                STEP_AUTH_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )