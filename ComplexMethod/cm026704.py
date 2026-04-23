async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Workday options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            combined_input: dict[str, Any] = {**self.config_entry.options, **user_input}
            if CONF_PROVINCE not in user_input:
                # Province not present, delete old value (if present) too
                combined_input.pop(CONF_PROVINCE, None)

            try:
                await self.hass.async_add_executor_job(
                    validate_custom_dates, combined_input
                )
            except AddDatesError:
                errors["add_holidays"] = "add_holiday_error"
            except AddDateRangeError:
                errors["add_holidays"] = "add_holiday_range_error"
            except RemoveDatesError:
                errors["remove_holidays"] = "remove_holiday_error"
            except RemoveDateRangeError:
                errors["remove_holidays"] = "remove_holiday_range_error"
            else:
                LOGGER.debug("abort_check in options with %s", combined_input)
                abort_match = {
                    CONF_COUNTRY: self.config_entry.options.get(CONF_COUNTRY),
                    CONF_EXCLUDES: combined_input[CONF_EXCLUDES],
                    CONF_OFFSET: combined_input[CONF_OFFSET],
                    CONF_WORKDAYS: combined_input[CONF_WORKDAYS],
                    CONF_ADD_HOLIDAYS: combined_input[CONF_ADD_HOLIDAYS],
                    CONF_REMOVE_HOLIDAYS: combined_input[CONF_REMOVE_HOLIDAYS],
                    CONF_PROVINCE: combined_input.get(CONF_PROVINCE),
                }
                if CONF_CATEGORY in combined_input:
                    abort_match[CONF_CATEGORY] = combined_input[CONF_CATEGORY]
                try:
                    self._async_abort_entries_match(abort_match)
                except AbortFlow as err:
                    errors = {"base": err.reason}
                else:
                    return self.async_create_entry(data=combined_input)

        options = self.config_entry.options
        schema: vol.Schema = await self.hass.async_add_executor_job(
            add_province_and_language_to_schema,
            DATA_SCHEMA_OPT,
            options.get(CONF_COUNTRY),
        )

        new_schema = self.add_suggested_values_to_schema(schema, user_input or options)
        LOGGER.debug("Errors have occurred in options %s", errors)
        return self.async_show_form(
            step_id="init",
            data_schema=new_schema,
            errors=errors,
            description_placeholders={
                "name": options[CONF_NAME],
                "country": options.get(CONF_COUNTRY, "-"),
            },
        )