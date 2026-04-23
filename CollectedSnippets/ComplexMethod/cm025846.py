async def async_step_ssdp_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle SSDP auth when credentials are required."""
        assert self.hostname is not None
        assert self.installation_id is not None

        errors: dict[str, str] = {}

        if user_input is not None:
            _LOGGER.debug(
                "SSDP auth user input received: %s",
                async_redact_data(user_input, TO_REDACT),
            )
            data: dict[str, Any] = {
                CONF_HOST: self.hostname,
                CONF_PORT: DEFAULT_PORT,
                CONF_SERIAL: self.serial,
                CONF_INSTALLATION_ID: self.installation_id,
                CONF_USERNAME: user_input.get(CONF_USERNAME),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD),
                CONF_SSL: user_input.get(CONF_SSL),
            }

            try:
                await validate_input(data)
                _LOGGER.debug("SSDP authentication successful")
            except AuthenticationError:
                _LOGGER.debug("Authentication failed during SSDP setup", exc_info=True)
                errors["base"] = "invalid_auth"
            except CannotConnectError:
                _LOGGER.debug("Cannot connect during SSDP setup", exc_info=True)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during SSDP setup")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=ENTRY_TITLE_FORMAT.format(
                        installation_id=self.installation_id,
                        host=self.hostname,
                        port=DEFAULT_PORT,
                    ),
                    data=data,
                )

        return self.async_show_form(
            step_id="ssdp_auth",
            data_schema=self.add_suggested_values_to_schema(
                STEP_SSDP_AUTH_DATA_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders={CONF_HOST: self.hostname},
        )