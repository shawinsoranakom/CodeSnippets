async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""

        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except RateLimitExceeded:
                errors["base"] = "rate_limit_exceeded"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                existing_entry = await self.async_set_unique_id(info["user_id"])
                if existing_entry:
                    await self.hass.config_entries.async_reload(existing_entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                return self.async_abort(reason="reauth_failed_existing")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=USER_DATA_SCHEMA,
            errors=errors,
        )