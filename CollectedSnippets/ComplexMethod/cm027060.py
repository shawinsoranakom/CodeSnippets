async def async_step_set_options(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Set conversation options."""
        # abort if entry is not loaded
        if self._get_entry().state != ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        errors: dict[str, str] = {}

        if user_input is None:
            if self._is_new:
                options: dict[str, Any]
                if self._subentry_type == "tts":
                    options = RECOMMENDED_TTS_OPTIONS.copy()
                elif self._subentry_type == "ai_task_data":
                    options = RECOMMENDED_AI_TASK_OPTIONS.copy()
                elif self._subentry_type == "stt":
                    options = RECOMMENDED_STT_OPTIONS.copy()
                else:
                    options = RECOMMENDED_CONVERSATION_OPTIONS.copy()
            else:
                # If this is a reconfiguration, we need to copy the existing options
                # so that we can show the current values in the form.
                options = self._get_reconfigure_subentry().data.copy()

            self.last_rendered_recommended = cast(
                bool, options.get(CONF_RECOMMENDED, False)
            )

        else:
            if user_input[CONF_RECOMMENDED] == self.last_rendered_recommended:
                if not user_input.get(CONF_LLM_HASS_API):
                    user_input.pop(CONF_LLM_HASS_API, None)
                # Don't allow to save options that enable the Google Search tool with an Assist API
                if not (
                    user_input.get(CONF_LLM_HASS_API)
                    and user_input.get(CONF_USE_GOOGLE_SEARCH_TOOL, False) is True
                ):
                    if self._is_new:
                        return self.async_create_entry(
                            title=user_input.pop(CONF_NAME),
                            data=user_input,
                        )

                    return self.async_update_and_abort(
                        self._get_entry(),
                        self._get_reconfigure_subentry(),
                        data=user_input,
                    )
                errors[CONF_USE_GOOGLE_SEARCH_TOOL] = "invalid_google_search_option"

            # Re-render the options again, now with the recommended options shown/hidden
            self.last_rendered_recommended = user_input[CONF_RECOMMENDED]

            options = user_input

        schema = await google_generative_ai_config_option_schema(
            self.hass, self._is_new, self._subentry_type, options, self._genai_client
        )
        return self.async_show_form(
            step_id="set_options", data_schema=vol.Schema(schema), errors=errors
        )