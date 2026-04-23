async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, Any] = {}

        if not self._all_region_codes_sorted:
            nina: Nina = Nina(async_get_clientsession(self.hass))

            try:
                self._all_region_codes_sorted = swap_key_value(
                    await nina.get_all_regional_codes()
                )
            except ApiError:
                return self.async_abort(reason="no_fetch")
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")

            self.regions = split_regions(self._all_region_codes_sorted, self.regions)

        if user_input is not None and not errors:
            user_input[CONF_REGIONS] = []

            for group in CONST_REGIONS:
                if group_input := user_input.get(group):
                    user_input[CONF_REGIONS] += group_input

            if not user_input[CONF_FILTERS][CONF_HEADLINE_FILTER]:
                user_input[CONF_FILTERS][CONF_HEADLINE_FILTER] = NO_MATCH_REGEX

            if user_input[CONF_REGIONS]:
                return self.async_create_entry(
                    title="NINA",
                    data=prepare_user_input(user_input, self._all_region_codes_sorted),
                )

            errors["base"] = "no_selection"

        default_filters = {
            CONF_FILTERS: {
                CONF_HEADLINE_FILTER: NO_MATCH_REGEX,
                CONF_AREA_FILTER: ALL_MATCH_REGEX,
            }
        }

        schema_with_suggested = self.add_suggested_values_to_schema(
            create_schema(self.regions), default_filters
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema_with_suggested,
            errors=errors,
        )