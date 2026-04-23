async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Generic IP Camera options."""
        errors: dict[str, str] = {}
        hass = self.hass

        if user_input:
            # Secondary validation because serialised vol can't seem to handle this complexity:
            if not user_input.get(CONF_STILL_IMAGE_URL) and not user_input.get(
                CONF_STREAM_SOURCE
            ):
                errors["base"] = "no_still_image_or_stream_url"
            else:
                errors, still_format = await async_test_still(hass, user_input)
                try:
                    self.preview_stream = await async_test_and_preview_stream(
                        hass, user_input
                    )
                except InvalidStreamException as err:
                    errors[CONF_STREAM_SOURCE] = str(err)
                    self.preview_stream = None
                if not errors:
                    data = {
                        **user_input,
                        CONF_CONTENT_TYPE: still_format
                        or self.config_entry.options.get(CONF_CONTENT_TYPE),
                    }
                    if (
                        CONF_USE_WALLCLOCK_AS_TIMESTAMPS
                        not in user_input[SECTION_ADVANCED]
                    ):
                        data[SECTION_ADVANCED][CONF_USE_WALLCLOCK_AS_TIMESTAMPS] = (
                            self.config_entry.options[SECTION_ADVANCED].get(
                                CONF_USE_WALLCLOCK_AS_TIMESTAMPS, False
                            )
                        )
                    self.user_input = data
                    # temporary preview for user to check the image
                    self.preview_image_settings = data
                    return await self.async_step_user_confirm()
        elif self.user_input:
            user_input = self.user_input
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                build_schema(
                    True,
                    self.show_advanced_options,
                ),
                user_input or self.config_entry.options,
            ),
            errors=errors,
        )