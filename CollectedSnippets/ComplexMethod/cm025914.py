async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a cloud based alarm."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if not self._reauth_entry:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()

            try:
                info = await validate_cloud_input(self.hass, user_input)
            except CannotConnectError:
                errors["base"] = "cannot_connect"
            except UnauthorizedError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if not self._reauth_entry:
                    return self.async_create_entry(title=info["title"], data=user_input)
                self.hass.config_entries.async_update_entry(
                    self._reauth_entry,
                    data=user_input,
                    unique_id=user_input[CONF_USERNAME],
                )
                await self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="cloud", data_schema=CLOUD_SCHEMA, errors=errors
        )