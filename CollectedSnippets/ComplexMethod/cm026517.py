async def async_step_location(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> SubentryFlowResult:
        """Handle the location step."""
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        if user_input is not None:
            exclude_id = (
                None if self._is_new else self._get_reconfigure_subentry().subentry_id
            )
            if _is_location_already_configured(
                self.hass, user_input[CONF_LOCATION], exclude_subentry_id=exclude_id
            ):
                return self.async_abort(reason="already_configured")
            api: GoogleWeatherApi = self._get_entry().runtime_data.api
            if await _validate_input(user_input, api, errors, description_placeholders):
                if self._is_new:
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data=user_input[CONF_LOCATION],
                    )
                return self.async_update_and_abort(
                    self._get_entry(),
                    self._get_reconfigure_subentry(),
                    title=user_input[CONF_NAME],
                    data=user_input[CONF_LOCATION],
                )
        elif self._is_new:
            user_input = {}
        else:
            subentry = self._get_reconfigure_subentry()
            user_input = {
                CONF_NAME: subentry.title,
                CONF_LOCATION: dict(subentry.data),
            }

        return self.async_show_form(
            step_id="location",
            data_schema=self.add_suggested_values_to_schema(
                _get_location_schema(self.hass), user_input
            ),
            errors=errors,
            description_placeholders=description_placeholders,
        )