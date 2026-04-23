async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            client = async_create_client(
                hass=self.hass,
                url=user_input[CONF_URL],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                verify_ssl=user_input.get(CONF_VERIFY_SSL, True),
            )

            # Check if we can connect to the WebDAV server
            # .check() already does the most of the error handling and will return True
            # if we can access the root directory
            try:
                result = await client.check()
            except UnauthorizedError:
                errors["base"] = "invalid_auth"
            except AccessDeniedError:
                errors["base"] = "access_denied"
            except MethodNotSupportedError:
                errors["base"] = "invalid_method"
            except Exception:
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                if result:
                    self._async_abort_entries_match(
                        {
                            CONF_URL: user_input[CONF_URL],
                            CONF_USERNAME: user_input[CONF_USERNAME],
                        }
                    )

                    parsed_url = yarl.URL(user_input[CONF_URL])
                    return self.async_create_entry(
                        title=f"{user_input[CONF_USERNAME]}@{parsed_url.host}",
                        data=user_input,
                    )

                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )