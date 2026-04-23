async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the start of the config flow."""
        errors = {}
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
                    user_input[CONF_CONTENT_TYPE] = still_format
                    still_url = user_input.get(CONF_STILL_IMAGE_URL)
                    stream_url = user_input.get(CONF_STREAM_SOURCE)
                    name = (
                        slug(hass, still_url) or slug(hass, stream_url) or DEFAULT_NAME
                    )
                    self.user_input = user_input
                    self.title = name
                    # temporary preview for user to check the image
                    self.preview_image_settings = user_input
                    return await self.async_step_user_confirm()
        elif self.user_input:
            user_input = self.user_input
        else:
            user_input = DEFAULT_DATA.copy()
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(build_schema(), user_input),
            errors=errors,
        )