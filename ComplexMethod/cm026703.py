async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle remaining flow."""
        errors: dict[str, str] = {}
        if user_input is not None:
            combined_input: dict[str, Any] = {**self.data, **user_input}

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

            abort_match = {
                CONF_COUNTRY: combined_input.get(CONF_COUNTRY),
                CONF_EXCLUDES: combined_input[CONF_EXCLUDES],
                CONF_OFFSET: combined_input[CONF_OFFSET],
                CONF_WORKDAYS: combined_input[CONF_WORKDAYS],
                CONF_ADD_HOLIDAYS: combined_input[CONF_ADD_HOLIDAYS],
                CONF_REMOVE_HOLIDAYS: combined_input[CONF_REMOVE_HOLIDAYS],
                CONF_PROVINCE: combined_input.get(CONF_PROVINCE),
            }
            if CONF_CATEGORY in combined_input:
                abort_match[CONF_CATEGORY] = combined_input[CONF_CATEGORY]
            LOGGER.debug("abort_check in options with %s", combined_input)
            self._async_abort_entries_match(abort_match)

            LOGGER.debug("Errors have occurred %s", errors)
            if not errors:
                LOGGER.debug("No duplicate, no errors, creating entry")
                return self.async_create_entry(
                    title=combined_input[CONF_NAME],
                    data={},
                    options=combined_input,
                )

        schema = await self.hass.async_add_executor_job(
            add_province_and_language_to_schema,
            DATA_SCHEMA_OPT,
            self.data.get(CONF_COUNTRY),
        )
        new_schema = self.add_suggested_values_to_schema(schema, user_input)
        return self.async_show_form(
            step_id="options",
            data_schema=new_schema,
            errors=errors,
            description_placeholders={
                "name": self.data[CONF_NAME],
                "country": self.data.get(CONF_COUNTRY, "-"),
            },
        )