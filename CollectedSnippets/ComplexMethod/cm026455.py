async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""
        errors: dict[str, str] = {}

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

            if user_input[CONF_REGIONS]:
                user_input = prepare_user_input(
                    user_input, self._all_region_codes_sorted
                )

                await self.remove_unused_entities(user_input)

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=user_input
                )

                return self.async_create_entry(title="", data={})

            errors["base"] = "no_selection"

        schema_with_suggested = self.add_suggested_values_to_schema(
            create_schema(self.regions), self.data
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema_with_suggested,
            errors=errors,
        )