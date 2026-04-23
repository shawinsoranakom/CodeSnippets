async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidUrl:
                errors[CONF_URL] = "invalid_url"
            except TimeoutConnectError:
                errors["base"] = "timeout_connect"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth as err:
                self.auth_header = err.metadata
                self.data[CONF_URL] = user_input[CONF_URL]
                return await self.async_step_auth_discovery()
            except MissingCapabilities:
                return self.async_abort(reason="missing_capabilities")
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={"example_url": EXAMPLE_URL},
        )